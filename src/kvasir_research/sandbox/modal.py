import modal
import shlex
import asyncio
import shutil
from pathlib import Path
from typing import AsyncGenerator, Tuple, Optional
from uuid import UUID

from kvasir_research.secrets import MODAL_APP_NAME, MODAL_PROJECTS_DIR, SANDBOX_DOCKERFILE_PATH, PROJECTS_DIR
from kvasir_research.sandbox.abstract import AbstractSandbox, create_empty_project_package_local
from kvasir_research.utils.code_utils import parse_code


app = modal.App.lookup(MODAL_APP_NAME, create_if_missing=True)


class ModalSandbox(AbstractSandbox):

    def __init__(self, project_id: UUID, package_name: str, image_name: str = "research-sandbox"):
        self.project_id = project_id
        self.package_name = package_name
        self.workdir = f"/app/{package_name}"
        self.vol = modal.Volume.from_name(
            str(project_id), create_if_missing=True)
        self.project_dir = MODAL_PROJECTS_DIR / str(self.project_id)
        self.sb: modal.Sandbox | None = None
        self.create_container_if_not_exists()

    def create_container_if_not_exists(self):
        with modal.enable_output():
            try:
                self.sb = modal.Sandbox.from_name(
                    MODAL_APP_NAME, str(self.project_id))
            except modal.exception.NotFoundError:
                try:
                    with self.vol.batch_upload() as batch:
                        batch.put_directory(f"{PROJECTS_DIR}/",
                                            f"/{PROJECTS_DIR.name}")
                except FileExistsError:
                    pass

                sandbox_image = modal.Image.from_dockerfile(
                    str(SANDBOX_DOCKERFILE_PATH))
                self.sb = modal.Sandbox.create(
                    image=sandbox_image,
                    app=app,
                    name=str(self.project_id),
                    volumes={"/app": self.vol},
                    timeout=24*60*60  # 24 hours
                )

    async def setup_project(self, package_name: str) -> Path:
        local_project_package_dir = create_empty_project_package_local(
            self.project_id, package_name)

        try:
            def _upload_directory():
                self.sb.terminate()
                self.sb.wait(raise_on_termination=False)
                with self.vol.batch_upload() as batch:
                    batch.put_directory(local_project_package_dir,
                                        f"/{local_project_package_dir.name}")

                # This is stupid, but the sandbox must terminate to reflect the changes in the volume
                sandbox_image = modal.Image.from_dockerfile(
                    str(SANDBOX_DOCKERFILE_PATH))
                self.sb = modal.Sandbox.create(
                    image=sandbox_image,
                    app=app,
                    name=str(self.project_id),
                    volumes={"/app": self.vol}
                )

            await asyncio.to_thread(_upload_directory)
        except FileExistsError:
            pass
        finally:
            shutil.rmtree(local_project_package_dir)

        _, err = await self.run_shell_code("pip install -e .")

        if err:
            raise RuntimeError(
                f"Failed to install package in container: {err}")

        return Path(f"/app/{package_name}")

    async def delete_container_if_exists(self):
        if self.sb:
            await self.sb.terminate.aio()
            self.sb = None

    async def run_python_code(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> Tuple[str, str]:
        python_code_parsed = parse_code(code)

        process = await self.sb.exec.aio(
            "python", "-c", "import sys; exec(sys.stdin.read())",
            timeout=timeout,
            workdir=self.workdir
        )

        process.stdin.write(python_code_parsed.encode('utf-8'))
        process.stdin.write_eof()
        await process.stdin.drain.aio()
        await process.wait.aio()
        out_str = process.stdout.read()
        err_str = process.stderr.read()

        if process.returncode != 0:
            err_str = err_str if err_str else ""
        else:
            err_str = ""

        if truncate_output and len(out_str) > max_output_length:
            keep_chars = max_output_length // 2
            truncation_msg = f"\n\n... [Output truncated: removed {len(out_str) - max_output_length:,} characters from middle, showing {max_output_length:,} of {len(out_str):,} total] ...\n\n"
            out_str = out_str[:keep_chars] + \
                truncation_msg + out_str[-keep_chars:]

        return out_str, err_str

    async def run_shell_code(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> Tuple[str, str]:
        shell_cmd = f"set -e; set -o pipefail;\n{code}"
        process = await self.sb.exec.aio(
            "bash", "-c", shell_cmd,
            timeout=timeout,
            workdir=self.workdir
        )

        await process.wait.aio()
        out_str = process.stdout.read()
        err_str = process.stderr.read()

        if process.returncode == 0:
            err_str = None
        else:
            err_str = err_str if err_str else ""

        if truncate_output and len(out_str) > max_output_length:
            keep_chars = max_output_length // 2
            truncation_msg = f"\n\n... [Output truncated: removed {len(out_str) - max_output_length:,} characters from middle, showing {max_output_length:,} of {len(out_str):,} total] ...\n\n"
            out_str = out_str[:keep_chars] + \
                truncation_msg + out_str[-keep_chars:]

        return out_str, err_str

    async def run_shell_code_streaming(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> AsyncGenerator[Tuple[str, str], None]:
        shell_cmd = f"set -e; set -o pipefail;\n{code}"
        process = await self.sb.exec.aio(
            "bash", "-c", shell_cmd,
            timeout=timeout,
            workdir=self.workdir
        )

        total_output_length = 0
        truncation_message_sent = False

        async def read_stdout():
            nonlocal total_output_length, truncation_message_sent
            async for line in process.stdout:
                if truncation_message_sent:
                    return
                content = line.decode(
                    'utf-8') if isinstance(line, bytes) else line.rstrip('\n\r')

                if truncate_output and len(content) > max_output_length:
                    keep_chars = max_output_length // 2
                    content = content[:keep_chars] + \
                        f"\n... [Line truncated: removed {len(content) - max_output_length:,} characters from middle] ...\n" + \
                        content[-keep_chars:]

                if truncate_output:
                    if total_output_length + len(content) > max_output_length:
                        yield ('stdout', f"\n\n... [Streaming output truncated: total output exceeded {max_output_length:,} characters, stopping stream] ...\n\n")
                        truncation_message_sent = True
                        return
                    total_output_length += len(content)

                yield ('stdout', content)

        async def read_stderr():
            nonlocal total_output_length, truncation_message_sent
            async for line in process.stderr:
                if truncation_message_sent:
                    return
                content = line.decode(
                    'utf-8') if isinstance(line, bytes) else line.rstrip('\n\r')

                if truncate_output and len(content) > max_output_length:
                    keep_chars = max_output_length // 2
                    content = content[:keep_chars] + \
                        f"\n... [Line truncated: removed {len(content) - max_output_length:,} characters from middle] ...\n" + \
                        content[-keep_chars:]

                if truncate_output:
                    if total_output_length + len(content) > max_output_length:
                        yield ('stderr', f"\n\n... [Streaming output truncated: total output exceeded {max_output_length:,} characters, stopping stream] ...\n\n")
                        truncation_message_sent = True
                        return
                    total_output_length += len(content)

                yield ('stderr', content)

        async def stream_all():
            stdout_gen = read_stdout()
            stderr_gen = read_stderr()

            pending = {
                asyncio.create_task(stdout_gen.__anext__()): stdout_gen,
                asyncio.create_task(stderr_gen.__anext__()): stderr_gen
            }

            try:
                while pending:
                    done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        gen = pending.pop(task)
                        try:
                            yield task.result()
                            pending[asyncio.create_task(gen.__anext__())] = gen
                        except StopAsyncIteration:
                            pass
            finally:
                for task in pending.keys():
                    task.cancel()

        try:
            async for item in stream_all():
                yield item
                if truncation_message_sent:
                    break
            await process.wait.aio()
            yield ('returncode', process.returncode)
        except Exception:
            yield ('returncode', -1)
            raise
        finally:
            if process.returncode is None:
                try:
                    await process.wait.aio()
                except Exception:
                    pass

    async def read_file(self, path: str, truncate: bool = True, max_output_length: int = 20000) -> str:
        quoted_path = shlex.quote(path)
        out, err = await self.run_shell_code(
            f"cat {quoted_path}",
            truncate_output=truncate,
            max_output_length=max_output_length
        )

        if err:
            raise RuntimeError(f"Failed to read file: {err}")

        return out

    async def write_file(self, path: str, content: str):
        quoted_path = shlex.quote(path)
        dir_path = shlex.quote(str(Path(path).parent))

        _, err = await self.run_shell_code(f"mkdir -p {dir_path}")
        if err:
            raise RuntimeError(f"Failed to create directory: {err}")

        process = await self.sb.exec.aio(
            "bash", "-c", f"cat > {quoted_path}",
            workdir=self.workdir
        )

        process.stdin.write(content.encode('utf-8'))
        process.stdin.write_eof()
        await process.stdin.drain.aio()
        await process.wait.aio()

        err_str = process.stderr.read()
        if process.returncode != 0:
            raise RuntimeError(
                f"Failed to write file: {err_str.decode('utf-8') if err_str else 'Unknown error'}")

    async def delete_file(self, path: str):
        quoted_path = shlex.quote(path)
        _, err = await self.run_shell_code(f"rm -rf {quoted_path}")

        if err:
            raise RuntimeError(f"Failed to delete file: {err}")

    async def rename_file(self, old_path: str, new_path: str):
        quoted_old_path = shlex.quote(old_path)
        quoted_new_path = shlex.quote(new_path)
        # Create directory for new path if it doesn't exist
        dir_path = shlex.quote(str(Path(new_path).parent))
        _, err = await self.run_shell_code(
            f"mkdir -p {dir_path} && mv {quoted_old_path} {quoted_new_path}"
        )

        if err:
            raise RuntimeError(f"Failed to rename file: {err}")

    async def check_file_exists(self, path: str) -> bool:
        quoted_path = shlex.quote(path)
        out, _ = await self.run_shell_code(
            f"test -f {quoted_path} && echo 'exists' || echo 'not_exists'",
            truncate_output=False
        )

        return out.strip() == "exists"

    async def get_working_directory(self) -> Tuple[str, str]:
        out, err = await self.run_shell_code("pwd", truncate_output=False)
        return out, err if err is not None else ""

    async def list_directory_contents(self, path: Optional[str] = None) -> Tuple[str, str]:
        if path is None:
            out, err = await self.run_shell_code("ls -la", truncate_output=False)
        else:
            quoted_path = shlex.quote(path)
            out, err = await self.run_shell_code(f"ls -la {quoted_path}", truncate_output=False)
        return out, err if err is not None else ""

    async def get_folder_structure(self, path: Optional[str] = None, n_levels: int = 5, max_lines: int = 100) -> str:
        if path:
            quoted_path = shlex.quote(path)
        else:
            quoted_path = "."

        find_cmd = f"find {quoted_path} -maxdepth {n_levels} \\( -name '__pycache__' -o -name '*.egg-info' \\) -prune -o -print 2>/dev/null | sort"
        out, err = await self.run_shell_code(find_cmd)

        if err:
            return f"folder structure {n_levels} levels down:\n\nError: {err}"

        if not out.strip():
            return f"folder structure {n_levels} levels down:\n\n(empty or does not exist)"

        all_paths = [line.rstrip('/')
                     for line in out.split('\n') if line.strip()]

        leaf_paths = []
        for current_path in all_paths:
            is_parent = False
            for other_path in all_paths:
                if other_path != current_path:
                    if other_path.startswith(current_path + '/'):
                        is_parent = True
                        break

            if not is_parent:
                leaf_paths.append(current_path)

        was_truncated = len(leaf_paths) > max_lines

        if was_truncated:
            result_lines = leaf_paths[:max_lines]
            result = '\n'.join(result_lines)
            return f"folder structure {n_levels} levels down:\n\n{result}\n\n[truncated - output exceeded {max_lines} lines]"
        else:
            result = '\n'.join(leaf_paths)
            return f"folder structure {n_levels} levels down:\n\n{result}"
