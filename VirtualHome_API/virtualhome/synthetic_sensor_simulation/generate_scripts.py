import sys
import json
import os
import re
import math

# Ensure we import the local virtualhome package (not the site-packages one)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from virtualhome import UnityCommunication
import IPython.display
import argparse

def load_actions_from_file(file_path):
    # Load script actions from a text file.
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]




def euclidean_distance(pos1, pos2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))




def load_json_file(file_path):
    """Load a JSON file and return it as a dictionary."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data



def extract_index_from_filename(filename):
    match = re.match(r"Action_(\d{4,5})_0_normal", filename)
    return int(match.group(1)) if match else None



def get_frame_indices(frames_base, before_set):
    after_set = {
        extract_index_from_filename(f)
        for f in os.listdir(frames_base)
        if f.endswith('.png') and extract_index_from_filename(f) is not None
    }
    new_indices = sorted(after_set - before_set)
    if new_indices:
        return new_indices[0], new_indices[-1]
    return None, None




def find_closest_object(current_position, object_name, graph):
    closest_obj = None
    min_distance = float('inf')

    for obj in graph:
        if obj.get("class_name") == object_name:
            obj_position = obj.get("obj_transform", {}).get("position", None)
            if obj_position is not None:
                distance = euclidean_distance(current_position, obj_position)
                if distance < min_distance:
                    min_distance = distance
                    closest_obj = obj

    if closest_obj:
        return (closest_obj.get("id"), closest_obj.get("properties", []))
    else:
        return (-1, [])




def find_room_id(room_name, graph):
    for obj in graph:
        if obj.get("category") == "Rooms" and obj.get("class_name") == room_name:
            return obj.get("id")
    return -1  # Return -1 if not found




def get_object_status(graph, object_id=None, class_name=None):
    for obj in graph:
        # Check by both ID and class_name if provided
        if (object_id is None or obj.get("id") == object_id) and \
           (class_name is None or obj.get("class_name") == class_name):
            print(f"Found object: id={obj.get('id')}, class_name={obj.get('class_name')}")
            print(f"States: {obj.get('states', [])}")
            return obj.get("states", [])
    print("Object not found.")
    return None





def find_current_position(graph):
    """
    Finds and returns the character's position from the given graph dictionary.
    
    Parameters:
        graph (dict): The graph dictionary containing a list of nodes.
        
    Returns:
        list or None: The position (e.g., [x, y, z]) of the character if found; otherwise, None.
    """
    for node in graph:
        # Check if this node represents a character (case-insensitive)
        if node.get("category", "").lower() == "characters":
            # Extract the position from the node's "obj_transform"
            obj_transform = node.get("obj_transform", {})
            position = obj_transform.get("position")
            return position
    # If no character node is found, return None.
    return None


def main(args):
    script_file = args.script_file
    environment_id = args.environment_id
    character = args.character
    initial_location = args.initial_room

    m = re.search(r'env_(\d+)_', os.path.basename(script_file))
    if not m:
        print(f"Couldn’t parse env_id from {script_file}, skipping.")
        return

    environment_id = int(m.group(1))

    file_name_prefix = f"{script_file}"

    room_match = re.search(r'_(bedroom|kitchen|bathroom|livingroom)\.txt$', script_file)
    if room_match:
        initial_location = room_match.group(1)
        print(f"🛏️ Using room `{initial_location}` as initial room based on filename.")
    else:
        print("⚠️ Could not extract room from filename, defaulting to bedroom.")
        initial_location = "bedroom"


    # Change this to the output directory you want to save the rendered output to
    output_dir = '/workspace/VirtualHome_API/virtualhome/rendered_output'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    # Initialize communication with Unity
    comm = UnityCommunication()

    # Reset the environment with the specified environment ID
    comm.reset(environment_id)

    # Add character
    comm.add_character(f'chars/{character}', initial_room=initial_location)

    # Get the environment graph
    # Should the add_sensors() function come before comm??
    s, graph = comm.environment_graph()

    # get the list of objects and rooms dictionary
    graph_sync = graph.get(f"nodes", [])

    # add sensors
    comm.add_sensors(environment_id)

    # Load actions from file or use default actions
    actions = load_actions_from_file(script_file)
    print(f"Total Routine Length: {len(actions)}")
    # Get the local graph, used for search id number
    # environment_path = os.path.join("environments", f"environment_graph_{environment_id}.json")
    # graph_dict = load_json_file(environment_path)
    # graph_local = graph_dict.get(f"nodes", [])

    # Set the variables to track the character's status at each action
    current_position = find_current_position(graph_sync)
    sitting = False # We need to check on this

    # stand up first
    stand_attempt_success = False

    for attempt in range(3):
        # Render the action
        success, message = comm.render_script(
            script= ["<char0> [standup]"],  # Pass the action as a single-item list
            processing_time_limit=60,
            find_solution=False,
            image_width=320,
            image_height=240,
            skip_animation=True,
            recording=False,
            save_pose_data=True,
            file_name_prefix=file_name_prefix,
            output_folder=output_dir
        )

        if success:
            stand_attempt_success = True
            break


    if stand_attempt_success:
        sitting = False
        graph_sync = message['environment_graph'].get(f"nodes", [])
        current_position = find_current_position(graph_sync)


    # Record final script
    final_script = []    
    executable_script = []

    frames_base = os.path.join(output_dir, file_name_prefix, "0")
    action_frame_ranges = []
    action_progress = 0
    # now start running on each action
    for action in actions:
        action_progress += 1
        verb_match = re.search(r'\[(.*?)\]', action)
        verb = verb_match.group(1) if verb_match else None

        # 2. Extract all objects (inside < >)
        objects = re.findall(r'<(.*?)>', action)

        # 3. Extract everything inside parentheses
        paren_contents = re.findall(r'\((.*?)\)', action)
        #    paren_contents[0] → timestamp "06:37 - 06:37"
        #    paren_contents[1] → room "bedroom"
        timestamp = paren_contents[0] if len(paren_contents) > 0 else None
        room = paren_contents[1] if len(paren_contents) > 1 else None

        if os.path.isdir(frames_base):
            before = {
                extract_index_from_filename(f)
                for f in os.listdir(frames_base)
                if f.endswith('.png') and extract_index_from_filename(f) is not None
            }
        else:
            before = set()
        
        if not verb:
            pass
        else: 
            if verb == "grab":

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                
                object_name = objects[0]
                

                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)



                # Walk to the object
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
                

                # Touch attempt
                touch_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [touch] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        touch_attempt_success = True
                        break


                if touch_attempt_success:
                    final_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
            
            







            elif verb in ["put", "putin"]:

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                

                object_name = objects[1]
                
                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)


                # Walk to the object
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
                

                # Touch attempt
                touch_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [touch] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        touch_attempt_success = True
                        break


                if touch_attempt_success:
                    final_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)    








            elif verb in ["walk", "walktowards"]:

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                
                # Check the object
                object_name = objects[0]
                id_number = -1

                if object_name in ["bedroom", "bathroom", "kitchen", "livingroom"]:
                    room_id = find_room_id(object_name, graph_sync)
                    id_number = room_id
                
                else:
                    object_id, object_property = find_closest_object(current_position, object_name, graph_sync)
                    id_number = object_id

                # Walk to the object/room
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({id_number})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({id_number})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({id_number})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
            








            elif verb == "run":

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                
                # Check the object
                object_name = objects[0]
                id_number = -1

                if object_name in ["bedroom", "bathroom", "kitchen", "livingroom"]:
                    room_id = find_room_id(object_name, graph_sync)
                    id_number = room_id
                
                else:
                    object_id, object_property = find_closest_object(current_position, object_name, graph_sync)
                    id_number = object_id

                # Run to the object/room
                run_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [run] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        run_attempt_success = True
                        break


                if run_attempt_success:
                    final_script.append(f"<char0> [run] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [run] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
            








            elif verb in ["walkforward", "turnleft", "turnright"]:

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)


                # Check three actions
                action_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [{verb}]"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        action_attempt_success = True
                        break


                if action_attempt_success:
                    final_script.append(f"<char0> [{verb}]")
                    executable_script.append(f"<char0> [{verb}]")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
            









            
            elif verb == "standup":

                if not sitting:
                    pass
                else:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)
            





            elif verb == "sit":
                if sitting:
                    pass
                
                object_name = objects[0]

                
                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)


                sit_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [sit] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        sit_attempt_success = True
                        break


                if sit_attempt_success:
                    sitting = True
                    final_script.append(f"<char0> [sit] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [sit] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)






            elif verb == "drink":

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                    else:
                        pass
                
                object_name = objects[0]
                
                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)



                # Walk to the object
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)


                # Look/touch/drink the object
                action_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [touch] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        action_attempt_success = True
                        break


                if action_attempt_success:
                    final_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
            



            elif verb in ["lookat", "touch"]:

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                    else:
                        pass
                
                object_name = objects[0]
                
                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)



                # Walk to the object
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)


                # Look/touch/drink the object
                action_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [{verb}] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        action_attempt_success = True
                        break


                if action_attempt_success:
                    final_script.append(f"<char0> [{verb}] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [{verb}] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)





            elif verb in ["open", "close"]:

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                    else:
                        pass

                object_name = objects[0]       
                
                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)

                object_state = get_object_status(graph_sync, object_id, object_name)
            
                if ("OPEN" not in object_state) and ("CLOSED" not in object_state):
                    pass

                if verb == "open" and "OPEN" in object_state:
                    pass

                if verb == "close" and "CLOSED" in object_state:
                    pass


                # Walk to the object
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
                


                # Open/close the object
                open_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [{verb}] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        open_attempt_success = True
                        break


                if open_attempt_success:
                    final_script.append(f"<char0> [{verb}] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [{verb}] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)







            elif verb in ["switchon", "switchoff"]:

                if sitting:
                    stand_attempt_success = False

                    for attempt in range(3):
                        # Render the action
                        success, message = comm.render_script(
                            script= ["<char0> [standup]"],  # Pass the action as a single-item list
                            processing_time_limit=60,
                            find_solution=True,
                            image_width=320,
                            image_height=240,
                            skip_animation=False,
                            recording=True,
                            save_pose_data=True,
                            file_name_prefix=file_name_prefix,
                            output_folder=output_dir
                        )

                        if success:
                            stand_attempt_success = True
                            break


                    if stand_attempt_success:
                        sitting = False
                        final_script.append("<char0> [standup]")
                        executable_script.append("<char0> [standup]")
                        graph_sync = message['environment_graph'].get(f"nodes", [])
                        current_position = find_current_position(graph_sync)

                    else:
                        pass

                object_name = objects[0]    
                
                object_id, object_property = find_closest_object(current_position, object_name, graph_sync)

                object_state = get_object_status(graph_sync, object_id, object_name)
            
                if ("ON" not in object_state) and ("OFF" not in object_state):
                    pass

                if verb == "switchon" and "ON" in object_state:
                    pass

                if verb == "switchoff" and "OFF" in object_state:
                    pass


                # Walk to the object
                walk_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [walk] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        walk_attempt_success = True
                        break


                if walk_attempt_success:
                    final_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [walk] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
                


                # Switchon/off the object
                switch_attempt_success = False

                for attempt in range(3):
                    # Render the action
                    success, message = comm.render_script(
                        script= [f"<char0> [touch] <{object_name}> ({object_id})"],  # Pass the action as a single-item list
                        processing_time_limit=60,
                        find_solution=True,
                        image_width=320,
                        image_height=240,
                        skip_animation=False,
                        recording=True,
                        save_pose_data=True,
                        file_name_prefix=file_name_prefix,
                        output_folder=output_dir
                    )

                    if success:
                        switch_attempt_success = True
                        break


                if switch_attempt_success:
                    final_script.append(f"<char0> [{verb}] <{object_name}> ({object_id})")
                    executable_script.append(f"<char0> [touch] <{object_name}> ({object_id})")
                    graph_sync = message['environment_graph'].get(f"nodes", [])
                    current_position = find_current_position(graph_sync)
        
        start_frame, end_frame = get_frame_indices(frames_base, before)
        action_frame_ranges.append((action, start_frame, end_frame))
        print(f"🔹 Action {action_progress} `{action}` → frames {start_frame} to {end_frame}")
            
    range_folder = os.path.join(output_dir)
    os.makedirs(range_folder, exist_ok=True)
    range_file = os.path.join(range_folder, f"range_{script_file}")

    with open(range_file, "w") as f:
        for action, start, end in action_frame_ranges:
            f.write(f"{action} ({start} - {end})\n")
    
    print(f"[AgentSense] All action‐frame ranges saved to {range_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate scripts for VirtualHome.")
    parser.add_argument('--script_file', type=str, default=None, help="Path to the text file containing script actions.")
    parser.add_argument('--environment_id', type=int, default=1, help="ID of the environment to reset.")
    parser.add_argument('--character', type=str, choices=['Male1', 'Male2', 'Female1', 'Female2'], default='Female2', help="Character to use in the simulation.")
    parser.add_argument('--initial_room', type=str, choices=['bedroom', 'kitchen', 'livingroom', 'bathroom'], default='bedroom', help="Initial room to use in the simulation.")
    args = parser.parse_args()

    main(args)

            
        

        
          

