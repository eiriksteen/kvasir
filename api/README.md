## Setting up development environment
First make sure to have the `app_secrets.py` file in both main_server and project_server folder.
In the folder HOME/.ssh/ run the following commands:
`openssl ecparam -genkey -name prime256v1 -noout -out ~/.ssh/es256-private.pem`
`openssl ec -in ~/.ssh/es256-private.pem -pubout -out ~/.ssh/es256-public.pem`
On some operating systems there is already a folder called es256-private.pem and es256-private.pem folder in "$HOME/.ssh/". Delete those folders.
Likewise these folders might exist under the main_server folder. Remove those as well.
If these are not removed you will get an error when trying to build the environment in docker.
To build the main-server environment navigate to the main_server folder and run the following command in terminal: `./run.ssh dev build`.

Once completed you can open a terminal inside the docker containers by running:
`docker exec -it main-server /bin/bash` (opens terminal in main-server container).
`docker exec -it main-db psql -U postgres -d kvasir` (opens a connection to the database).

Inside the database connection run `CREATE EXTENSION vector;`.
Inside the main-server terminal run `alembic upgrade head`.
Inside the main-server terminal run `pip install "bcrypt==4.0.1"`. The later versions of bcrypt does not support some hashing required by JWT.

For the api to work you also need to make sure you have a `.env.local` file.

To build the project-server environment navigate to the project_server folder an run the following command in terminal: `./run.ssh dev build`.
What about cache?
You should now have a fully working dev environment.