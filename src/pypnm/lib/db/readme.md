# This is a readme file for the database library of the PyPNM project.
# TODO: Need to migrate the existing DB functionality to this directory.
# for Now we are going to work on JSON read/write functionality.

# JSON Read/Write Functionality

```json
{
    "<transaction_id>": {
        "timestamp":,
        "filename": "<filename>.json",
        "sha256": "<file+timestamp-sha256-hash>",
        }
    },
}

```

Create a class that handles reading and writing JSON files for database transactions.

read_json(file_path: str) -> Dict[str, Any]
write_json(file_path: str, data: Dict[str, Any]) -> None
use SystemConfigSettings for configuration management.

Use FileProcessor from pypnm.lib.file_processor for file operations.
Need a method call to read teh json-db and return the data as a dictionary.


