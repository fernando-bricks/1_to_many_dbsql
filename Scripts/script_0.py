# Databricks notebook source
# Databricks notebook, Python

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import pipelines
from databricks.sdk.service.pipelines import PipelineLibrary, NotebookLibrary, FileLibrary

# 1. Get workspace URL (often used as workspace name indicator)
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
# If you want only the short name part, you can do:
workspace_name = workspace_url.split('.')[0]

print(f"Workspace URL: {workspace_url}")
print(f"Workspace name: {workspace_name}")

# 2. Initialize Databricks SDK client
w = WorkspaceClient()

# 3. Get current user to build catalog name "<user>_workshop"
me = w.current_user.me()  # returns current user info [web:12]
# Often user_name is the login/email; you can sanitize as needed
raw_username = me.user_name

# Simple sanitization for catalog name: lowercase, replace disallowed chars
import re
base_name = raw_username.split("@")[0].lower()
base_name = re.sub(r"[^a-z0-9_]", "_", base_name)

catalog_name = "dbacademy"
schema_name = base_name
volume_name = "files"

print(f"Catalog to create: {catalog_name}")
print(f"Schema to create:  {schema_name}")
print(f"Volume to create:  {volume_name}")

# COMMAND ----------

# DBTITLE 1,Cell 1
# 4. Create catalog if it does not exist
from databricks.sdk.errors import NotFound

try:
    _ = w.catalogs.get(name=catalog_name)
    print(f"Catalog '{catalog_name}' already exists.")
except NotFound:
    created_catalog = w.catalogs.create(
        name=catalog_name,
        comment=f"Workshop catalog for {raw_username} in workspace {workspace_name}"
    )  # catalogs.create usage pattern [web:1][web:11]
    print(f"Created catalog '{created_catalog.name}'.")

# 5. Create schema 'coffee_shop' in that catalog (if not exists)
try:
    _ = w.schemas.get(full_name=f"{catalog_name}.{schema_name}")
    print(f"Schema '{catalog_name}.{schema_name}' already exists.")
except NotFound:
    created_schema = w.schemas.create(
        name=schema_name,
        catalog_name=catalog_name,
        comment="Schema for coffee shop workshop objects"
    )  # schemas.create usage pattern [web:11]
    print(f"Created schema '{created_schema.full_name}'.")

# 6. Create managed volume 'files' in that schema (if not exists)
#    VolumeType.MANAGED lets UC handle storage in the default location. [web:1]
from databricks.sdk.errors import ResourceAlreadyExists

try:
    created_volume = w.volumes.create(
        catalog_name=catalog_name,
        schema_name=schema_name,
        name=volume_name,
        volume_type=VolumeType.MANAGED,
        comment="Workshop files volume"
    )  # volumes.create usage pattern [web:1]
    print(f"Created volume '{created_volume.full_name}'.")
except ResourceAlreadyExists:
    print(f"Volume '{catalog_name}.{schema_name}.{volume_name}' already exists.")

# COMMAND ----------

#7 creating pipline root

pipeline_root = f"/Workspace/Users/{raw_username}/DBSQL_Workshop/Transformation"

# Create subfolders inside the root folder
w.workspace.mkdirs(f"{pipeline_root}/transformations")
w.workspace.mkdirs(f"{pipeline_root}/explorations")
w.workspace.mkdirs(f"{pipeline_root}/tests")

pipeline_name = "workshop_coffee_shop_pipeline"

pipeline = w.pipelines.create(
    name=pipeline_name,
    catalog=catalog_name,
    target=schema_name,            # UC schema in that catalog (preferred over legacy `target`) [web:25]
    development=True,
    continuous=False,
    channel="CURRENT",
    serverless=True,
    libraries=[
        PipelineLibrary(file=FileLibrary(path=f"{pipeline_root}/transformations/raw_layer.py")),
         PipelineLibrary(file=FileLibrary(path=f"{pipeline_root}/transformations/silver_layer.py")),
         PipelineLibrary(file=FileLibrary(path=f"{pipeline_root}/transformations/gold_layer.py"))
    ],             # Enable serverless compute for the pipeline [web:25][web:40]
    configuration={
        # Optional pipeline parameters, available as Spark conf
        "pipeline.etl_mode": "full_refresh",
        "param.volume": f"/Volumes/{catalog_name}/{schema_name}/{volume_name}"
    }
)

print(f"Created serverless pipeline '{pipeline_name}' with id: {pipeline.pipeline_id}")

# COMMAND ----------

# DBTITLE 1,Copy subfolders from workspace to volume
# Copy subfolders and their contents from workspace folder to Unity Catalog volume
import os
import base64
from databricks.sdk.service.workspace import ObjectType

def copy_folder_to_volume(w, source_folder, destination_folder, verbose=True):
    """
    Recursively copy a workspace folder and all its subfolders to a Unity Catalog volume.
    
    Args:
        w: WorkspaceClient instance
        source_folder: Source path in /Workspace
        destination_folder: Destination path in /Volumes
        verbose: Print progress messages
    """
    if verbose:
        print(f"Copying from {source_folder} to {destination_folder}")
    
    try:
        # List all items in the source folder
        items = w.workspace.list(source_folder)
        
        for item in items:
            item_name = item.path.split('/')[-1]
            dest_path = f"{destination_folder}/{item_name}"
            
            if item.object_type == ObjectType.DIRECTORY:
                # Create subfolder in volume
                try:
                    os.makedirs(dest_path, exist_ok=True)
                    if verbose:
                        print(f"Created folder: {dest_path}")
                except Exception as e:
                    if verbose:
                        print(f"Folder may already exist: {dest_path}")
                
                # Recursively copy subfolder contents
                copy_folder_to_volume(w, item.path, dest_path, verbose)
                
            elif item.object_type == ObjectType.FILE:
                # Export file content from workspace
                exported = w.workspace.export(item.path)
                
                # Decode base64 content if encoded
                if hasattr(exported, 'content'):
                    content = base64.b64decode(exported.content)
                else:
                    content = exported
                
                # Write to volume
                with open(dest_path, 'wb') as f:
                    f.write(content)
                
                if verbose:
                    print(f"Copied file: {item_name}")
        
        if verbose:
            print(f"\nCompleted copying {source_folder}")
            
    except Exception as e:
        print(f"Error copying {source_folder}: {e}")
        raise

# Example usage: Copy Assets folder with all subfolders to volume
source_folder = f"/Workspace/Users/{raw_username}/DBSQL_Workshop/Assets"
destination_folder = f"/Volumes/{catalog_name}/{schema_name}/{volume_name}"

copy_folder_to_volume(w, source_folder, destination_folder, verbose=True)