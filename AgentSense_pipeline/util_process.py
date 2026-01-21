import re
import numpy as np

def process_location_sequences(file_path):
    virtual_aruba_Dict = {
        0: 'Bed_To_Toilet', 1: 'Eat', 2: 'Housekeeping', 3: 'Leave_Home',
        4: 'Meal_Preparation', 5: 'Other', 6: 'Relax', 7: 'Sleeping', 8: 'Work'
    }
    virtual_milan_Dict = {
        0: 'Bed_To_Toilet', 1: 'Chores', 2: 'Dining_Rm_Activity', 3: 'Guest_Bathroom',
        4: 'Kitchen_Activity', 5: 'Leave_Home', 6: 'Master_Bathroom', 7: 'Master_Bedroom_Activity',
        8: 'Meditate', 9: 'Other', 10: 'Read', 11: 'Sleep'
    }
    virtual_cairo_Dict = {
        0: 'Bed_To_Toilet', 1: 'Breakfast', 2: 'Dinner', 3: 'Leave_Home',
        4: 'Lunch', 5: 'Night_Wandering', 6: 'Other', 7: 'Sleep',
        8: 'Take_Meds', 9: 'Wake', 10: 'Work_in_Office'
    }
    virtual_kyoto7_Dict = {
        0: "other",
        1: "clean",
        2: "meal_preparation",  
        3: "bed_to_toilet",
        4: "personal_hygiene",
        5: "sleep",
        6: "work",
    7: "study",
    8: "wash_bathtub",
    9: "watch_TV"
    }
    virtual_orange_Dict = {0: "Other", 1: "Bathroom|Cleaning", 2: "Bathroom|Showering", 3: "Bathroom|Using_the_sink", 4: "Bathroom|Using_the_toilet", 5: "Bedroom|Cleaning", 6: "Bedroom|Dressing", 7: "Bedroom|Napping", 
                           8: "Bedroom|Reading", 9: "Entrance|Entering", 10: "Entrance|Leaving", 11: "Kitchen|Cleaning", 12: "Kitchen|Cooking", 13: "Kitchen|Preparing", 14: "Kitchen|Washing_the_dishes", 15: "Living_room|Cleaning", 
                           16: "Living_room|Computing", 17: "Living_room|Eating", 18: "Living_room|Watching_TV", 19: "Office|Cleaning", 20: "Office|Computing", 21: "Office|Watching_TV", 22: "Staircase|Going_down", 
                           23: "Staircase|Going_up", 24: "Toilet|Using_the_toilet"}


    aruba_map = {v.lower(): k for k, v in virtual_aruba_Dict.items()}
    milan_map = {v.lower(): k for k, v in virtual_milan_Dict.items()}
    cairo_map = {v.lower(): k for k, v in virtual_cairo_Dict.items()}
    kyoto7_map = {v.lower(): k for k, v in virtual_kyoto7_Dict.items()}
    orange_map = {v.lower(): k for k, v in virtual_orange_Dict.items()}

    tuple_sequence = []
    frame_indices = []

    with open(file_path, 'r') as f:
        for line in f:
            matches = re.findall(r'\((.*?)\)', line)
            # print(matches)
            if len(matches) >= 4:
                loc_str = matches[2]  # the (Aruba, Milan, Cairo) group
                idx_str = matches[3]  # the (start - end) group

                parts = [x.strip().lower() for x in loc_str.split(',')]
                if len(parts) != 5:
                    continue

                try:
                    start, end = map(int, idx_str.split('-'))
                except:
                    continue

                tuple_sequence.append(tuple(parts))
                frame_indices.append((start, end))

    if not tuple_sequence:
        print("No valid (Aruba, Milan, Cairo) tuples found.")
        return [], [], [], []

    # Group consecutive identical tuples and accumulate their frame ranges
    grouped = []
    frame_ranges = []
    current_group = [tuple_sequence[0]]
    current_range = list(frame_indices[0])

    for i in range(1, len(tuple_sequence)):
        if tuple_sequence[i] == current_group[-1]:
            current_group.append(tuple_sequence[i])
            current_range[1] = frame_indices[i][1]  # extend end frame
        else:
            grouped.append(current_group)
            frame_ranges.append(tuple(current_range))
            current_group = [tuple_sequence[i]]
            current_range = list(frame_indices[i])

    grouped.append(current_group)
    frame_ranges.append(tuple(current_range))

    # Collapse and convert to integer class labels
    collapsed = [g[0] for g in grouped]
    aruba_seq = [aruba_map.get(t[0], -1) for t in collapsed]
    milan_seq = [milan_map.get(t[1], -1) for t in collapsed]
    cairo_seq = [cairo_map.get(t[2], -1) for t in collapsed]
    kyoto7_seq = [kyoto7_map.get(t[3], -1) for t in collapsed]
    orange_seq = [orange_map.get(t[4], -1) for t in collapsed]

    return aruba_seq, milan_seq, cairo_seq, kyoto7_seq, orange_seq, frame_ranges

def segment_by_frame_intervals(frames, state_list, sensor_list, timestamp_list):
    """
    Segments the state, sensor, and timestamp lists based on given frame ranges.

    Args:
        frames: list of (start_frame, end_frame) tuples
        state_list: list of ON/OFF strings (e.g. "ON", "OFF")
        sensor_list: list of sensor names (same length as state_list)
        timestamp_list: list of frame indices (same length as state_list)

    Returns:
        (seg_states, seg_sensors, seg_timestamps) — each a list of lists, aligned to frames
    """
    seg_states = []
    seg_sensors = []
    seg_timestamps = []

    for start, end in frames:
        states = []
        sensors = []
        times = []

        for state, sensor, time in zip(state_list, sensor_list, timestamp_list):
            if isinstance(time, int):
                in_range = start <= time <= end
            elif hasattr(time, "second"):  # datetime
                # optional: skip datetime support
                in_range = False
            else:
                in_range = False

            if in_range:
                states.append(state)
                sensors.append(sensor)
                times.append(time)

        seg_states.append(states)
        seg_sensors.append(sensors)
        seg_timestamps.append(times)

    return seg_states, seg_sensors, seg_timestamps


from datetime import datetime, timedelta
import random

def map_timestamps_to_datetimes(time_list, txt_path):
    """
    Maps timestamps to datetime.datetime objects using HH:MM from the file.
    Ensures chronological order is preserved at the second level.

    Args:
        time_list: list[int] — frame indices
        txt_path: str — label file path

    Returns:
        list[datetime.datetime]
    """
    mapping = []

    # Step 1: Parse the txt file for timestamp-to-time mappings
    with open(txt_path, "r") as f:
        for line in f:
            try:
                # Extract (...) blocks
                parens = [part.split(')')[0] for part in line.split('(') if ')' in part]
                if len(parens) < 3:
                    continue

                time_range = parens[0]
                index_range = parens[-1]

                if 'None' in index_range:
                    continue

                hhmm = time_range.split('-')[0].strip()
                hour, minute = map(int, hhmm.split(':'))
                start_idx, end_idx = map(int, index_range.strip().split('-'))

                mapping.append((start_idx, end_idx, hour, minute))

            except Exception as e:
                print(f"Skipping line due to parsing error: {line.strip()} — {e}")

    # Step 2: Map each timestamp
    result = []
    last_dt = None

    for ts in time_list:
        match = next(((h, m) for start, end, h, m in mapping if start <= ts <= end), None)

        if match is None:
            result.append(None)
            continue

        hour, minute = match

        # If hour/minute increased, reset second to random 0–59
        if last_dt is None or (hour, minute) > (last_dt.hour, last_dt.minute):
            second = random.randint(0, 59)
        else:
            # Keep going up in seconds within the same minute
            second = last_dt.second + 10
            if second >= 60:
                # Overflow → bump to next minute safely
                minute += 1
                second = second - 60
                if minute >= 60:
                    hour += 1
                    minute = minute - 60
                    if hour >= 24:
                        hour = hour - 24

        microsecond = random.randint(0, 999999)
        dt = datetime(2010, 11, 4, hour, minute, second, microsecond)

        last_dt = dt
        result.append(dt)

    return result

def extract_sensor_transitions_with_timestamps(unique_sensor_positions, index_to_time=None, min_gap=20):
    """
    Detects ON/OFF transitions using magnitude of sensor readings.
    A transition is ON when magnitude > 0, OFF when below, merged with min_gap.

    Parameters:
        unique_sensor_positions (dict): {
            sensor_name: [(x, y, z, index), ...]
        }
        index_to_time (dict, optional): { index: timestamp }
        min_gap (int): min index gap to separate two clusters

    Returns:
        Tuple: (state_list, sensor_list, time_list)
    """
    import numpy as np
    from collections import defaultdict


    state_list = []
    sensor_list = []
    time_list = []

    for sensor_name, positions in unique_sensor_positions.items():
        # Build a list of (index, magnitude)
        mag_by_index = defaultdict(float)
        for x, y, z, idx in positions:
            mag = np.sqrt(x**2 + y**2 + z**2)
            if mag > 0:
                mag_by_index[idx] = mag  # keep max mag if duplicate

        on_indices = sorted(mag_by_index.keys())
        if not on_indices:
            continue

        # Merge intervals with min_gap
        intervals = []
        start = on_indices[0]
        prev = on_indices[0]

        for idx in on_indices[1:]:
            if idx - prev >= min_gap:
                intervals.append((start, prev))
                start = idx
            prev = idx
        intervals.append((start, prev))

        # Add transitions
        for start_idx, end_idx in intervals:
            state_list.append("ON")
            sensor_list.append(sensor_name)
            time_list.append(index_to_time[start_idx] if index_to_time else start_idx)

            state_list.append("OFF")
            sensor_list.append(sensor_name)
            time_list.append(index_to_time[end_idx + 1] if index_to_time else end_idx + 1)

    return state_list, sensor_list, time_list



def get_sensor_positions(file_path, num_lines=100000):
    """
    Reads the motion sensor data file and returns a list of dictionaries.
    Each dictionary has:
      - key: sensor name (constructed from parts[1] and parts[2])
      - value: list of unique position tuples (part[4], part[5], part[6], part[0])
    
    Parameters:
        file_path (str): Path to the motion sensor data file.
        num_lines (int): Maximum number of lines to process.
    
    Returns:
        list: A list of dictionaries, each representing a sensor and its position data.
              Example:
              [
                {"Female2 MotionSensor_PRE_ROO_Bedroom_00_f675df77-7cdf-406a-abd0-a3b32c9559f9": 
                    [(-8.611, -0.01441101, -4.830191, 12), ...]
                },
                {...},
                ...
              ]
    """
    sensor_dict = {}

    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_lines:
                break
            parts = line.strip().split()
            if len(parts) < 7:
                continue  # Skip invalid lines
            
            # Construct sensor name key: e.g., "Female2 MotionSensor_PRE_ROO_Bedroom_00_f675df77-7cdf-406a-abd0-a3b32c9559f9"
            sensor = f"{parts[1]} {parts[2]}"
            
            # Create the tuple: (x, y, z, index) from parts[4], parts[5], parts[6], and parts[0]
            try:
                pos_tuple = (float(parts[4]), float(parts[5]), float(parts[6]), int(parts[0]))
            except ValueError:
                continue  # Skip the line if conversion fails
            
            # Initialize list if sensor not seen before
            if sensor not in sensor_dict:
                sensor_dict[sensor] = []
            
            # Append the tuple only if it is not already present (ensuring uniqueness)
            if pos_tuple not in sensor_dict[sensor]:
                sensor_dict[sensor].append(pos_tuple)
    
    # Convert the sensor dictionary into a list of dictionaries (one per sensor)
    return sensor_dict

def get_unique_sensors(file_path, num_lines=100000):
    """
    Reads the given file and returns a list of unique sensor IDs, which are assumed to be
    the third field on each line (index 2), preserving the order of their first appearance.
    
    Parameters:
        file_path (str): Path to the motion sensor data text file.
        num_lines (int): Maximum number of lines to process.
        
    Returns:
        list: A list of unique sensor IDs.
    """
    unique_sensors = []
    
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_lines:
                break
            parts = line.strip().split()
            if len(parts) < 3:
                continue  # Skip lines that don't have enough parts
            sensor = parts[2]
            if sensor not in unique_sensors:
                unique_sensors.append(sensor)
                
    return unique_sensors


def process_motion_data_unique(file_path, num_lines=100000):
    """
    Process a motion sensor data file by removing the sensor ID (the third field)
    if it has already appeared in any previous line.
    
    Parameters:
        file_path (str): Path to the motion sensor data file.
        num_lines (int): Maximum number of lines to process.
        
    Returns:
        list: A list of processed lines with duplicate sensor IDs removed.
    """
    processed_lines = []
    seen_sensors = set()  # To keep track of sensor IDs we have seen

    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_lines:
                break

            line = line.strip()
            if not line:
                continue

            # Split the line into parts; assuming format:
            # <index> <character> <sensor_id> <room> <x> <y> <z> ... 
            parts = line.split()
            if len(parts) < 4:
                processed_lines.append(line)
                continue

            sensor = parts[2]  # The sensor ID is the third field (index 2)
            if sensor in seen_sensors:
                continue
            else:
                seen_sensors.add(sensor)
            
    return seen_sensors




def process_virtual_data(file_path, txt_path):
    """
    Process virtual sensor data and segment it based on frame intervals.
    
    Parameters:
        file_path (str): Path to the motion sensor data file
        txt_path (str): Path to the range/label file
        
    Returns:
        tuple: (seg_states, seg_sensors, seg_timestamps, aruba_seq, milan_seq, cairo_seq)
            - seg_states: List of state sequences for each segment
            - seg_sensors: List of sensor sequences for each segment  
            - seg_timestamps: List of timestamp sequences for each segment
            - aruba_seq: Activity sequence for Aruba
            - milan_seq: Activity sequence for Milan
            - cairo_seq: Activity sequence for Cairo
    """
    # Get sensor positions and transitions
    unique_sensor_positions = get_sensor_positions(file_path, num_lines=100000)
    state_list, sensor_list, time_list = extract_sensor_transitions_with_timestamps(unique_sensor_positions)

    # Process location sequences
    aruba_seq, milan_seq, cairo_seq, kyoto7_seq, orange_seq, frame_ranges = process_location_sequences(txt_path)

    # Segment data by frame intervals
    seg_states, seg_sensors, seg_timestamps = segment_by_frame_intervals(frame_ranges, state_list, sensor_list, time_list)

    # Map timestamps to datetimes
    seg_timestamps = [map_timestamps_to_datetimes(x, txt_path=txt_path) for x in seg_timestamps]

    return seg_states, seg_sensors, seg_timestamps, aruba_seq, milan_seq, cairo_seq, kyoto7_seq, orange_seq



import os
import re
from pathlib import Path

def combine_txt_files_with_frame_adjustment(file_paths, output_name="combined_output.txt"):
    """
    Combines multiple .txt files from a list of paths, adjusting the (start - end) frame
    range in each line so that the second file continues from where the first ended.

    Args:
        file_paths: List of paths to input .txt files
        output_name: Name of the output combined file (saved to home directory)
    """
    if not file_paths:
        print("❌ No files provided.")
        return

    output_lines = []
    current_frame = 0

    for file_index, file_path in enumerate(file_paths):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                match = re.findall(r'\((\d+)\s*-\s*(\d+)\)', line)
                if not match:
                    output_lines.append(line)
                    continue

                # Assume last (start - end) is the frame range
                original_start, original_end = map(int, match[-1])
                if file_index == 0:
                    updated_start = original_start
                    updated_end = original_end
                else:
                    updated_start = current_frame + 1
                    updated_end = updated_start + (original_end - original_start)

                # Replace only the last (start - end) in the line
                line = re.sub(r'\(\d+\s*-\s*\d+\)(?!.*\(\d+\s*-\s*\d+\))',
                              f'({updated_start} - {updated_end})', line)

                current_frame = updated_end
                output_lines.append(line)

        except Exception as e:
            print(f"⚠️ Skipping file {file_path} due to error: {e}")

    with open(output_name, 'w', encoding='utf-8') as out_file:
        out_file.writelines(output_lines)

    print(f"\n[AgentSense] Combined activity-to-frame-range mapping files saved to: {output_name}")



import os

def combine_sensor_txt_files(file_paths, output_name="combined_motion_sensors.txt"):
    if not file_paths:
        print("❌ No files provided.")
        return

    combined_lines = []
    last_written_index = -1

    for file_index, file_path in enumerate(file_paths):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        valid_lines = [line for line in lines if line.strip() and len(line.strip().split()) >= 7]
        if not valid_lines:
            print("⚠️ No valid lines found in this file. Skipping.")
            continue

        try:
            base_index = int(valid_lines[0].strip().split()[0])
        except ValueError:
            continue

        # Track max index seen in this file to update last_written_index once
        max_relative_index = 0
        for i, line in enumerate(valid_lines):
            parts = line.strip().split()
            try:
                original_index = int(parts[0])
            except ValueError:
                print(f"   ⚠️ Skipping malformed line {i}: {line.strip()}")
                continue

            relative_index = original_index - base_index
            new_index = last_written_index + 1 + relative_index
            max_relative_index = max(max_relative_index, relative_index)

            parts[0] = str(new_index)
            combined_lines.append(" ".join(parts))

        last_written_index += max_relative_index + 1

    with open(output_name, 'w', encoding='utf-8') as f_out:
        f_out.write("\n".join(combined_lines) + "\n")

    print(f"[AgentSense] Combined motion location data written to: {output_name}")