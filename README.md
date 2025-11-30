## EmberAlert Backend
This is a FastAPI-powered service that collects, stores, and serves wildfire incident data from the Cal Fire public API. It provides a clean REST interface for retrieving fire information. The backend consists of a scheduler, the API server, and a PostgreSQL database. Each component is containerized and deployed to an EC2 instance.

### API Server
The API server exposes REST endpoints for retrieving wildfire incident data stored in the database. It also provides WebSocket connections for real-time notification handling, allowing clients to receive updates as wildfire events change. Built with FastAPI, it serves as the main interface for external applications such as mobile or web clients.

## Tech Stack
> This project's backend is built using the following core technologies:

<div align="center">
    <img src="https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="Postgres" />
    <img src="https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
    <img src="https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS" />
</div>

---


## Backend Setup

### Docker Setup

Docker is required to set up and run the backend.
You can find the compose file in the following repository:

👉 [CMPE-195-Capstone: Compose](https://github.com/cmpe-195-capstone-project/compose)

Clone the repository to access the `docker-compose.yml`.

The compose file is available here: . Please clone the repo to access the docker compose file


### Image Versions
The compose file uses the latest `backend` and `scheduler` images for `linux/amd64` platforms.
If you need `linux/arm64`, update the image fields in the compose file to:

```yaml
scheduler:
    image: carlosqmv/scheduler:linux-amd64
    ...


backend:
    image: carlosqmv/backend:linux-amd64
```
Docker Hub links for reference:

- Backend: https://hub.docker.com/r/carlosqmv/backend  
- Scheduler: https://hub.docker.com/r/carlosqmv/scheduler
> **Note**: Numeric image tags are associated with `linux/amd64` platforms.
`linux-arm64` tags are for `linux/arm64` platforms.

---

### Database Initialization
The `init.sql` script is executed automatically when the Postgres container is created.
It sets up the required tables and initial schema for an EmberAlert testing database.  

---

### Run
> **Note**: Make sure you are in the directory containing both the docker-compose.yml and init.sql files before running the Docker commands.
Start the services using:

```shell
docker compose up -d
```
