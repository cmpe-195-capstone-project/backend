## Setup
### 1. Create and Run The Scheduler Application First
- [Ember Alert Scheduler](https://github.com/AliciaZhao/Ember-Alert/blob/scheduler/scheduler/README.md)
> The scheduler populates the database used for the main server & you need the database to be running for this to work.

## 2. Change into Server Directory
```shell
cd server
```
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

DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres
```

### 5. Run FastAPI app
```shell
uvicorn main:app --reload 
```
> Access the FastAPI at `localhost:8000` and the Swagger UI interface at `localhost:8000/docs`
# backend
