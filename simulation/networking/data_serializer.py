import json

class DataSerializer:
    @staticmethod
    def serialize_renderer_data(renderer_data):
        # Convert to JSON string, then encode to bytes
        json_string = json.dumps(renderer_data, indent=4)
        return json_string.encode("utf-8")

    @staticmethod
    def deserialize_renderer_data(data_bytes):
        # Decode bytes to string, then parse JSON
        json_string = data_bytes.decode("utf-8")
        return json.loads(json_string)