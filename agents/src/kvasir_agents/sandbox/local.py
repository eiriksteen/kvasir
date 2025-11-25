import asyncio
import docker
from uuid import UUID
from pathlib import Path
from typing import AsyncGenerator, Tuple
from docker.errors import NotFound, ImageNotFound

from kvasir_agents.sandbox.abstract import AbstractSandbox, create_empty_project_package_local
from kvasir_agents.utils.code_utils import parse_code
from kvasir_agents.app_secrets import (
    CODEBASE_HOST_DIR,
    PROJECTS_HOST_DIR,
    PROJECTS_DIR
)


class LocalSandbox(AbstractSandbox):
    def __init__(self, project_id: UUID, package_name: str, image_name: str = "research-sandbox"):
        self.project_id = project_id
        self.package_name = package_name
        self.workdir = f"/app/{package_name}"
        self.image_name = image_name
        self.container_name = str(project_id)
        self.create_container_if_not_exists()

    def create_container_if_not_exists(self):
        docker_client = docker.from_env()

        try:
            existing_container = docker_client.containers.get(
                self.container_name)
            if existing_container.status != "running":
                existing_container.start()
        except NotFound:
            project_dir = CODEBASE_HOST_DIR / str(self.project_id)
            if not project_dir.exists():
                project_dir.mkdir(parents=True, exist_ok=True)

            try:
                docker_client.images.get(self.image_name)
            except ImageNotFound as e:
                raise RuntimeError(
                    f"Sandbox image {self.image_name} not found, the image must be built first") from e

            container = docker_client.containers.create(
                image=self.image_name,
                name=self.container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                working_dir="/app",
                volumes={str(project_dir): {"bind": "/app", "mode": "rw"},
                         str(PROJECTS_HOST_DIR): {"bind": str(PROJECTS_DIR), "mode": "ro"}}
            )
            container.start()

    async def setup_project(self) -> Path:
        create_empty_project_package_local(self.project_id, self.package_name)

        _, err = await self.run_shell_code(
            "pip install -e ."
        )

        if err:
            raise RuntimeError(
                f"Failed to install package in container: {err}")

        return Path(f"/app/{self.package_name}")

    async def delete_container_if_exists(self):
        docker_client = docker.from_env()

        try:
            existing_container = docker_client.containers.get(
                self.container_name)
            if existing_container:
                existing_container.stop()
                existing_container.remove()
        except NotFound:
            pass

    async def run_python_code(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> Tuple[str, str]:
        python_code_parsed = parse_code(code)

        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && python -c 'import sys; exec(sys.stdin.read())'"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            if timeout is not None:
                try:
                    out, err = await asyncio.wait_for(
                        process.communicate(
                            python_code_parsed.encode('utf-8')),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    # Timeout occurred - kill the process
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()

                    timeout_msg = f"Process exceeded timeout of {timeout}s and was terminated"
                    return "", timeout_msg
            else:
                out, err = await process.communicate(python_code_parsed.encode('utf-8'))
        finally:
            # Ensure process is cleaned up
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass

        err_str = err.decode("utf-8") if process.returncode != 0 else ""
        out_str = out.decode("utf-8")

        # Truncate output if requested and too long
        if truncate_output and len(out_str) > max_output_length:
            # Keep beginning and end, truncate middle
            keep_chars = max_output_length // 2
            truncation_msg = f"\n\n... [Output truncated: removed {len(out_str) - max_output_length:,} characters from middle, showing {max_output_length:,} of {len(out_str):,} total] ...\n\n"
            out_str = out_str[:keep_chars] + \
                truncation_msg + out_str[-keep_chars:]

        return out_str, err_str

    async def run_shell_code(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> Tuple[str, str]:
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && set -e; set -o pipefail;\n{code}"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            if timeout:
                try:
                    out, err = await asyncio.wait_for(process.communicate(), timeout=timeout)
                except asyncio.TimeoutError:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                    return "", f"Process exceeded timeout of {timeout}s and was terminated"
            else:
                out, err = await process.communicate()
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass

        err_str = None if process.returncode == 0 else err.decode("utf-8")
        out_str = out.decode("utf-8")

        # Truncate output if requested and too long
        if truncate_output and len(out_str) > max_output_length:
            # Keep beginning and end, truncate middle
            keep_chars = max_output_length // 2
            truncation_msg = f"\n\n... [Output truncated: removed {len(out_str) - max_output_length:,} characters from middle, showing {max_output_length:,} of {len(out_str):,} total] ...\n\n"
            out_str = out_str[:keep_chars] + \
                truncation_msg + out_str[-keep_chars:]

        return out_str, err_str

    async def run_shell_code_streaming(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> AsyncGenerator[Tuple[str, str], None]:
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && set -e; set -o pipefail;\n{code}"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        if process.stdin:
            process.stdin.close()

        total_output_length = 0
        truncation_message_sent = False

        async def read_stream(stream, stream_type):
            nonlocal total_output_length, truncation_message_sent
            while True:
                line = await stream.readline()
                if not line:
                    break
                content = line.decode("utf-8").rstrip('\n\r')

                # Truncate individual line if too long
                if truncate_output and len(content) > max_output_length:
                    keep_chars = max_output_length // 2
                    content = content[:keep_chars] + \
                        f"\n... [Line truncated: removed {len(content) - max_output_length:,} characters from middle] ...\n" + \
                        content[-keep_chars:]

                if truncate_output:
                    if truncation_message_sent:
                        return
                    if total_output_length + len(content) > max_output_length:
                        yield (stream_type, f"\n\n... [Streaming output truncated: total output exceeded {max_output_length:,} characters, stopping stream] ...\n\n")
                        truncation_message_sent = True
                        return
                    total_output_length += len(content)

                yield (stream_type, content)

        async def stream_all():
            stdout_gen = read_stream(process.stdout, "stdout")
            stderr_gen = read_stream(process.stderr, "stderr")

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
            if timeout:
                try:
                    async with asyncio.timeout(timeout):
                        async for item in stream_all():
                            yield item
                            if truncation_message_sent:
                                break
                        await process.wait()
                        yield ('returncode', process.returncode)
                except asyncio.TimeoutError:
                    yield ('timeout', f'Process exceeded timeout of {timeout}s')
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                    yield ('returncode', -1)
            else:
                async for item in stream_all():
                    yield item
                    if truncation_message_sent:
                        break
                await process.wait()
                yield ('returncode', process.returncode)
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass

    async def read_file(self, path: str, truncate: bool = True, max_output_length: int = 20000) -> str:
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && cat {path}"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(
                f"Failed to read file from container: {err.decode('utf-8')}")

        content = out.decode("utf-8")

        # Truncate output if requested and too long
        if truncate and len(content) > max_output_length:
            # Keep beginning and end, truncate middle
            keep_chars = max_output_length // 2
            truncation_msg = f"\n\n... [Output truncated: removed {len(content) - max_output_length:,} characters from middle, showing {max_output_length:,} of {len(content):,} total] ...\n\n"
            content = content[:keep_chars] + \
                truncation_msg + content[-keep_chars:]

        return content

    async def write_file(self, path: str, content: str):
        escaped_content = content.replace("'", "'\\''")

        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && mkdir -p $(dirname {path}) && touch {path} && echo '{escaped_content}' > {path}"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(
                f"Failed to write file to container: {err.decode('utf-8')}")

        return out.decode("utf-8")

    async def delete_file(self, path: str):
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && rm -rf {path}"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()

        return out.decode("utf-8"), err.decode("utf-8")

    async def rename_file(self, old_path: str, new_path: str):
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && mv {old_path} {new_path}"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()

        return out.decode("utf-8"), err.decode("utf-8")

    async def check_file_exists(self, path: str) -> bool:
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && test -f {path} && echo 'exists' || echo 'not_exists'"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, _ = await process.communicate()

        return out.decode("utf-8").strip() == "exists"

    async def get_working_directory(self) -> Tuple[str, str]:
        cmd = [
            "docker", "exec", "-i",
            self.container_name,
            "bash", "-c", f"cd {self.workdir} && pwd"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()

        return out.decode("utf-8"), err.decode("utf-8")

    async def list_directory_contents(self, path: str = None) -> Tuple[str, str]:
        if path is None:
            cmd = [
                "docker", "exec", "-i",
                self.container_name,
                "bash", "-c", f"cd {self.workdir} && ls -la"
            ]
        else:
            cmd = [
                "docker", "exec", "-i",
                self.container_name,
                "bash", "-c", f"cd {self.workdir} && ls -la {path}"
            ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()

        return out.decode("utf-8"), err.decode("utf-8")

    async def get_folder_structure(self, path: str = "/app", n_levels: int = 5, max_lines: int = 100) -> str:
        find_cmd = f"find {path} -maxdepth {n_levels} \\( -name '__pycache__' -o -name '*.egg-info' \\) -prune -o -print 2>/dev/null | sort"
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
                    # Check if other_path is a child of current_path
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
