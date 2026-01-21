import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import json
import argparse
import re

def load_api_key(file_path='api_key.txt'):
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('api_key='):
                return line.strip().split('=', 1)[1]
    return None

os.environ["OPENAI_API_KEY"] = load_api_key()


class LangChainActions:
    def __init__(self, env):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        with open('tools/actions.json') as actions_json:
            self.actions = json.load(actions_json)

        with open('tools/rooms.json') as rooms_json:
            self.rooms = json.load(rooms_json)

        with open('tools/objects.json') as objects_json:
            self.objects = json.load(objects_json)

        with open('tools/graph_config.json') as config_json:
            self.config = json.load(config_json)
        
        self.object_index = FAISS.load_local("tools/objects_index", self.embeddings, allow_dangerous_deserialization=True)
        self.room_index = FAISS.load_local("tools/room_index", self.embeddings, allow_dangerous_deserialization=True)
        self.action_index = FAISS.load_local("tools/actions_index", self.embeddings, allow_dangerous_deserialization=True)

        self.object_index.delete(self.objects.keys())


        # all object's that's in env_# will have at least one room in "rooms"
        # resulting metadata:
        # [
        #     {"rooms": ["livingroom", "bedroom"], "keyword": "rug"},
        #     {"rooms": ["bathroom", "bedroom"], "keyword": "ceilinglamp"}
        # ]
        metadatas = []
        for key in self.objects.keys():
            room_metadata = {"rooms": [], "keyword": self.objects[key]['keyword']}
            for x in self.config[f'env_{env}']:
                if x['class_name'] == self.objects[key]['keyword']:
                    for room in x['rooms']:
                        room_metadata['rooms'].append(room['class_name'])
            metadatas.append(room_metadata)


        self.object_index.add_texts(
            self.objects.keys(),
            ids=self.objects.keys(),
            metadatas=metadatas
        )
    
    def get_action(self, action):
        action_key = self.action_index.similarity_search_with_relevance_scores(action, k=1)
        if action_key[0][1] >= 0.8:
            return action_key[0][0].page_content
        # action_key = [
        #     (ActionPage(page_content="[sit]"), 0.95)  # A tuple of the match and its relevance score
        # ]
        return None

    def get_room(self, room):
        room_key = self.room_index.similarity_search_with_relevance_scores(room, k=1)
        if room_key[0][1] >= 0.9:
            return room_key[0][0].page_content
        return None
    
    #based on the object in the certain env to do embeddings.
    def get_object(self, object, filter=None):
        object_key = self.object_index.similarity_search_with_relevance_scores(object, k=1, filter=filter)
        if len(object_key) == 0:
            return None
        # object_key = [
        #     (ObjectPage(metadata={"keyword": "rug"}), 0.85)
        # ]
        if object_key[0][1] >= 0.6:
            return object_key[0][0].metadata['keyword']
        return None

# Ground one parsed routine file into VirtualHome-valid actions/objects and save as *_grounded.txt.
def ground_single_routine_file(input_file_path: str, output_dir: str):

    if not os.path.isfile(input_file_path):
        print(f"[AgentSense][Error] Input file not found: {input_file_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    file_name = os.path.basename(input_file_path)

    # Extract env_id from filename like: "...env_0..."
    env_match = re.search(r'env_(\d+)', file_name)
    if not env_match:
        print(f"[AgentSense][Error] Could not find env ID in filename: {file_name}")
        print("[AgentSense][Hint] Make sure filename contains pattern like 'env_0'.")
        return

    env_id = int(env_match.group(1))
    langchain_actions = LangChainActions(env_id)

    valid_rooms = {"bathroom", "bedroom", "kitchen", "livingroom"}

    with open(input_file_path, "r", encoding="utf-8") as f:
        routine_content = f.read()

    grounded_text = ""

    for line in routine_content.splitlines():
        # Keep block separation
        if not line.startswith("["):
            grounded_text += "\n"
            continue

        line = line.strip()

        # Find room (location at end of line)
        room_match = re.search(r"\(([^()]*)\)\s*$", line)
        if not room_match:
            continue
        location = room_match.group(1).lower()

        # Find action in [ ... ]
        action_match = re.search(r"\[(.*?)\]", line)
        if not action_match:
            continue
        action = action_match.group(1)

        action_key = langchain_actions.get_action(action)
        if action_key is None:
            grounded_text += "[]\n"
            continue

        grounded_text += f"[{action_key}] "

        # Extract time range
        time_match = re.search(r"\((\d{1,2}:\d{2} - \d{1,2}:\d{2})\)", line)
        time_range = time_match.group(1) if time_match else "unknown"

        # Ground objects
        objects = re.findall(r"<(.*?)>", line)
        for obj in objects:
            obj_norm = obj.lower().replace("_", "").replace(" ", "")

            # Rooms are allowed directly
            if obj_norm in valid_rooms:
                grounded_text += f"<{obj_norm}> "
                continue

            object_key = langchain_actions.get_object(
                obj_norm,
                filter=lambda metadata: location in metadata["rooms"]
            )
            if object_key is None:
                grounded_text += "<> "
                continue

            grounded_text += f"<{object_key}> "

        grounded_text += f"({time_range}) ({location})\n"

    # Save as *_grounded.txt
    base_name = os.path.splitext(file_name)[0]
    output_file_name = f"{base_name}_grounded.txt"
    output_path = os.path.join(output_dir, output_file_name)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(grounded_text)

    print(f"[AgentSense] Grounding finished.")
    print(f"[AgentSense] env_id = {env_id}")
    print(f"[AgentSense] Output saved to: {output_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Step 6: Ground one parsed routine file to VirtualHome-valid actions/objects."
    )

    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Path to a single Step 5 parsed routine file (e.g., Sarah_routine_env_0_Monday_parsed.txt)"
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory to save the grounded routine output (*_grounded.txt)"
    )

    args = parser.parse_args()

    ground_single_routine_file(
        input_file_path=args.input_file,
        output_dir=args.output_dir
    )
