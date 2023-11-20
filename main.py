'''Author: Mausam Rajbanshi (AI Developer)'''
import aiofiles
import os

from decouple import config
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse

from utils.utils import fast_scandir, latest_version


app = FastAPI(title="Directory Management")

# declaring the directory where html templates resides
templates = Jinja2Templates(directory="templates")

# static password stored in env file    #Technology@123
static_password = {'username':config('user_name'), 'password':config('password')}

# ROOT_DIR = os.path.join(os.path.abspath('.'), 'projects')
ROOT_DIR = os.path.join(os.path.dirname(__file__), 'projects')
os.makedirs(ROOT_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('home.html',context={"request": request})

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse('login.html',context={"request": request})

@app.post("/dirManager", response_class=HTMLResponse)
def authenticated(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == static_password["username"] and password == static_password["password"]:
        # authenticated
        # scans for directories in project directory
        directories = fast_scandir(ROOT_DIR)
        
        return templates.TemplateResponse(
            'dirManager.html',
            context={"request": request, "directories":directories}
        )
    else:
        # return "Username and password mismatch"
        return templates.TemplateResponse(
            'redirect.html',
            context={"request": request, "url":"/login"}
        )

@app.post("/create", response_class=HTMLResponse)    
def create_dir(request: Request, dirName: str = Form(...)):

    # create directory in reference to root dir 
    dir_to_create = os.path.join(ROOT_DIR, dirName)

    if os.path.exists(dir_to_create) and os.path.isdir(dir_to_create):
        msg = f"Project named `{dirName}` already exists."
    else:
        os.makedirs(dir_to_create, exist_ok=True)
        msg = f"Created directory `{dir_to_create}`."

    # scans for directories in project directory
    directories = fast_scandir(ROOT_DIR)
    return templates.TemplateResponse(
            'dirManager.html',
            context={"request": request, "directories":directories, 'created': msg}
        )

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, selectDir:str = Form(...), selectFile: UploadFile = File(...)):
    update = None
    filename = selectFile.filename  # extract filename from uploaded file

    filepath = os.path.join(selectDir, filename)    # create filepath 

    # format filepath for version-control file `update.txt`
    filename_parts = filename.split('.')[0].split('_')
    txt_filename = filename_parts[0] + '.txt'
    txt_filepath = os.path.join(selectDir, txt_filename)

    # only upload when new version is available 
    if os.path.exists(txt_filepath) and os.path.isfile(txt_filepath):
        available_version = latest_version(txt_filepath)
        new_version = int(filename_parts[1][1:])
        update = True if new_version > available_version else False

    # also upload when there is no version
    if not os.listdir(selectDir):
        update = True

    if update:
        # store the bin file 
        async with aiofiles.open(filepath, 'wb') as f:
            while content_chunk := await selectFile.read(1024):
                await f.write(content_chunk)
        
        # update/create update.txt file
        async with aiofiles.open(txt_filepath, 'w') as update_f:
            await update_f.write(filename_parts[1]+'\n')

        msg = f"Uploaded file `{filepath}`.\nUpdated file {txt_filepath}."
    else:
        msg = "Upload terminated due to lower or same version of uploaded file."

    # scans for directories in project directory
    directories = fast_scandir(ROOT_DIR)
    
    return templates.TemplateResponse(
            'dirManager.html',
            context={"request": request, "directories":directories, "uploaded":msg}
        )

@app.get("/version")
def get_version(project_name):
    '''Returns the latest version'''
    project_vc = os.path.join(ROOT_DIR, project_name, 'update.txt')

    if os.path.exists(project_vc) and os.path.isfile(project_vc):
        available_version = latest_version(project_vc)
        return available_version
    else:
        return None


# @app.get('/download')     # call http://127.0.0.1:8000/download?project_name=d&version=v0
@app.get('/download/{project_name}/{version}')      # call http://127.0.0.1:8000/download/project_name/version
def download(project_name:str, version:str):
    '''downloads project file for requested version'''
    file_location = os.path.join(ROOT_DIR, project_name, "update.txt")

    # update.txt filepath validation
    try:
        assert os.path.exists(file_location)
        assert os.path.isfile(file_location)
    except AssertionError as e:
        return "Please check the project path."
    
    # requested version validation
    # wanted_version = version[1:] if version.isalnum() else version if version.isnumeric() else None
    try:
        assert version.isalnum()
        assert version.startswith('v')
        wanted_version = version[1:]
        assert wanted_version.isnumeric()
        wanted_version = int(wanted_version)
    except Exception as e:
        print(f"{e = }")
        return 'Erorr occured: '+str(e)

    # bin filename and filepath formation
    file_name = f"update_v{wanted_version}.bin"
    file_location = os.path.join(ROOT_DIR, project_name, file_name)

    # download if filepath indicates file and it exists
    if os.path.exists(file_location) and os.path.isfile(file_location):
        return FileResponse(file_location, media_type='application/octet-stream', filename=file_name)
    
    return "Requested file not available"

