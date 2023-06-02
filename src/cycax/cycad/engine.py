import json


class Engine:
    def __init__(self) -> None:
        pass

    def add(self, part):
        """This adds a new object into the assembly and decodes it into a json if that's what the user wants"""
        jsonFile = open(part.part_no + ".json", "w")
        jsonStr = json.dumps(part.export(), indent=4)
        jsonFile.write(jsonStr)
        jsonFile.close()
