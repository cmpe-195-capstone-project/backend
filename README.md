## Setup

## 1. Create Database
```shell
docker run --name test_db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=test_db -p 5434:5432 -d postgres:17
```
> Access Postgresql Shell: `docker exec -it test_db psql -U postgres -d test_db`

### 2. Create Virtual Environment
```shell
python3 -m venv venv
```

### 3. Activate Virtual Environment
- **On Mac/Linux:**
```shell
source venv/bin/activate
```

- **On Windows:**
```shell
venv\Scripts\activate
```
> To turn off virtual environment run `deactivate` on terminal

### 4. Install Dependencies
```shell
pip install -r requirements.txt
```

### 5. Adding Environment Variables
- Ensure a `.env` file is present in the `/server` directory
- Add the following lines to `.env` file
```
API_URL=https://incidents.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=true
TEST_DB_URL='postgresql://postgres:postgres@localhost:5434/test_db'
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres
```

### 6. Run FastAPI app
```shell
uvicorn main:app --reload 
```
> Access the FastAPI at `localhost:8000` and the Swagger UI interface at `localhost:8000/docs`
