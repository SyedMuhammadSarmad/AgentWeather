from dotenv import load_dotenv
import hopsworks
import os

load_dotenv()
Hopswork_api_key = os.getenv("Hopswork_api_key")
Hopswork_project = os.getenv("Hopswork_project")


project = hopsworks.login(api_key_value = Hopswork_api_key, project= Hopswork_project)

fs = project.get_feature_store()

print("Connected: ", fs.name)



