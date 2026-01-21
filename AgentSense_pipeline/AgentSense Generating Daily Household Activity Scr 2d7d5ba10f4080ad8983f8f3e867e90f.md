# AgentSense: Generating Daily Household Activity Scripts Using Large Language Models

# Prerequisite: OpenAI API Setup (Required for Most Steps)

Most steps in this pipeline require access to the OpenAI API for large language model inference.

## 1. Clone the repository

Clone the AgentSense repository to your local machine or server, then navigate into the cloned repository directory.

```bash
git clone <REPO_URL>
cd <REPO_NAME>
```

This pipeline for generating daily household activity scripts is contained in the `AgentSense_pipeline` folder. Ensure that the following files and folders are present inside this directory:

- `prompts/`
- `data/`
- `tools/`
- api_key.txt
- room_objects.json
- evaluation.ipynb
- step_1_personality_generation.ipynb
- step_2_schedule_generation.ipynb
- step_3_routine_generation.ipynb
- step_4_split_by_day.ipynb
- step_5_clean_daily_routines.ipynb
- step_6_action_grouding.py
- step_7_regeneration.ipynb
- step_8_label_generation.ipynb
- step_9_split_by_block.ipynb
- step_11_generate_npy_files.ipynb
- util_process.py

## 2. Prepare your OpenAI API key

You will find a file named `api_key.txt` in the directory.
The file content should be formatted **exactly** as follows (no quotes, no extra spaces):

```
api_key=your_openai_api_key_here
```

Simply copy your OpenAI API key and paste it after `api_key=`.
Do not commit your real API key to GitHub.

# Step 1: Personality Generation

This step generates synthetic personalities using a large language model (**GPT-4o-mini**).

Each generated personality serves as the foundation for downstream schedule and routine script generation in subsequent steps.

The implementation for this step is contained in the following Jupyter Notebook:

```
step_1_personality_generation.ipynb
```

## 1. Open the notebook

From the `AgentSense_pipeline` directory, launch Jupyter Notebook:

```bash
jupyter notebook
```

Then open:

```
step_1_personality_generation.ipynb
```

## 2. Run all setup cells

Execute the notebook cells **from top to bottom**.

These cells will:

- Import required libraries
- Load your OpenAI API key from `api_key.txt`
- Initialize the OpenAI client
- Define helper functions for prompt loading and personality generation

**Do not skip any cells**, as later cells depend on earlier definitions.

## 3. Prompt configuration

Personality generation prompts are stored separately for clarity and reproducibility.

- Prompt files are located in the `prompts/` directory
- The default prompt file used in this step is:

```
prompts/personality_generation_prompt.txt
```

## 4. User-editable configuration (final cell)

The **last cell of the notebook** is the only part most users need to modify.

You may change:

- Where the generated data is saved
- The output file name
- The prompt directory
- The number of personalities generated in one run (**we recommend at most 5 at a time**)

## 5. Select and Save a Personality for Schedule Generation

In the subsequent steps of the pipeline, schedules and routines are generated based on **one personality at a time**.

Therefore, you must first select a single personality that you find interesting and save it as an individual file.

### What to do

1. **Review the generated personality text**
    
    After running Step 1, open the generated personality output file (e.g., `personality_generated.txt`) and read through the description.
    
2. **Choose one personality**
    
    Select the personality you want to use for downstream schedule and routine generation.
    
3. **Create a new personality file**
    
    Create a new `.txt` file containing **only the selected personality description**.
    
4. **Name the file using the character’s name**
    
    The file must follow this naming format:
    
    ```
    {character_name}_personality.txt
    ```
    
    We **strongly recommend** using this naming convention. For all subsequent steps, please continue to follow the provided naming conventions, as several parts of the pipeline rely on information encoded in file names (e.g., character name, environment ID, and day). In later stages—especially during simulator execution—the code also infers location context directly from file names. Adhering to the naming convention ensures that all steps run correctly and that files can be processed and combined reliably.
    
    **Example:**
    
    - If the selected character’s name is **Sarah**
    - The file name should be:
        
        ```
        Sarah_personality.txt
        ```
        
5. **Save the file in the personality directory**
    
    Place the file in the directory used for personality inputs (e.g., `step_1_personality_data/` or your configured personality folder).
    

### Example personality file content

**File name:**

```
Sarah_personality.txt
```

**File content:**

```
Sarah, she is 34 years old, a graphic designer, and has thefollowing health situation: none. Sarah leads a vibrant lifestyle filled with creativity; she regularly practices yoga and enjoys healthy cooking. Her passion for art is evident in her vibrant personality, often radiating positivity and energy. Sarah is known for her attention to detail, and she thrives on collaboration, frequently organizing team outings to spark creativity among her peers.
```

# Step 2: Schedule Generation

This step generates a synthetic weekly schedule based on a personality you selected in **Step 1** using a large language model (**GPT-4o-mini**).

Each generated schedule serves as the foundation for downstream routine **(schedule activity breakdown)** script generation in the next step.

The implementation for this step is contained in the following Jupyter Notebook:

```
step_2_schedule_generation.ipynb
```

The workflow for this step is similar to the previous step. Open the Jupyter Notebook and run **all cells from top to bottom** without skipping any.

You may need to modify the **final cell**, where you can specify:

- The directory containing the schedule generation prompt
- The output directory for the generated schedule
- The personality file (`{character_name}_personality.txt`) you want to use to generate the weekly schedule

The generated schedule will be saved as

```
{character_name}_weekly_schedule.txt
```

It contains the character’s schedule from Monday through Sunday. We **highly recommend keeping** this file naming format unchanged.

You can see an example below:

```
Monday: 
wake_up (07:12 - 07:15) (at home) 
brushing_teeth (07:15 - 07:21) (at home) 
yoga_practice (07:21 - 07:50) (at home) 
showering (07:50 - 08:10) (at home) 
breakfast_preparation (08:10 - 08:38) (at home) 
healthy_breakfast (08:38 - 08:55) (at home) 
commuting_to_work (08:55 - 09:32) (outside) 
arriving_at_office (09:32 - 09:37) (outside) 
checking_emails (09:37 - 10:15) (outside) 
...
reading_a_book (22:00 - 23:00) (at home) 
going_to_the_bathroom (23:00 - 23:05) (at home) 
brushing_teeth (23:05 - 23:15) (at home) 
sleep (23:15 - 06:15) (at home)
 
Tuesday: 
wake_up (06:15 - 06:20) (at home) 
brushing_teeth (06:20 - 06:26) (at home) 
yoga_practice (06:26 - 06:54) (at home) 
showering (06:54 - 07:10) (at home) 
breakfast_smoothie (07:10 - 07:38) (at home) 
commuting_to_work (07:38 - 08:21) (outside) 
...

Wednesday:
...

Thursday:
...

Friday:
...

Saturday:
...

Sunday:
...
```

# Step 3: Routine Generation

This step generates daily routine (schedule activity breakdown) scripts based on the weekly schedule produced in Step 2 and the personality description you selected in Step 1.

For example, if you selected `Sarah_personality.txt` in Step 1 and generated `Sarah_weekly_schedule.txt` in Step 2, Step 3 will use both the personality and the corresponding weekly schedule as references to generate detailed breakdowns for each activity **marked as “at home”** in the schedule (referred to here as *routines*), using a large language model (**GPT-4o-mini**).

Each generated routine script translates high-level schedule entries into fine-grained, temporally ordered activity routines, with all action verbs and objects constrained to the VirtualHome libraries and compatible with the selected environment, enabling downstream simulation, sensor synthesis, or behavior modeling.

The implementation for this step is contained in the following Jupyter Notebook:

```
step_3_routine_generation.ipynb
```

The workflow for this step is similar to previous steps. Open the Jupyter Notebook and run all cells from top to bottom without skipping any.

You may need to modify the **final cell**, where you can specify:

- The directory containing the routine generation prompt
- The output directory for the generated routine script
- The VirtualHome environment to use (recommended environments are provided in the final cell to ensure simulator stability and consistent room layouts; you can inspect each environment’s objects and number of rooms in `room_objects.json`).
- The personality file (`{character_name}_personality.txt`) and schedule file (`{character_name}_weekly_schedule.txt`) you want to use to generate the routine script (please ensure both files correspond to the same synthetic character)

The generated routine script will be saved as

```
{character_name}_routine_env_{#}.txt
```

It contains the character’s routine breakdown from Monday through Sunday. We **highly recommend keeping** this file naming format unchanged.

You can see an example below. The activities **wake_up** and **brushing_teeth**, generated in **Step 2**, have been broken down into detailed steps.

```
Monday:
07:12 - 07:15, bedroom: wake_up

07:12 - 07:13, bedroom  
Step 1: [sit] <bed> (07:12 - 07:12)  
Step 2: [standup] (07:12 - 07:13)  

07:13 - 07:14, bedroom  
Step 1: [walk] <nightstand> (07:13 - 07:13)  
Step 2: [grab] <cellphone> (07:13 - 07:14)  

07:14 - 07:15, bedroom  
Step 1: [put] <cellphone> <nightstand> (07:14 - 07:14)  
Step 2: [walk] <window> (07:14 - 07:15)  
Step 3: [open] <curtains> (07:15 - 07:15)

07:15 - 07:21, bathroom: brushing_teeth

07:15 - 07:17, bathroom  
Step 1: [walk] <bathroom> (07:15 - 07:15)  
Step 2: [switchon] <lightswitch> (07:15 - 07:15)  
Step 3: [walk] <bathroomcounter> (07:15 - 07:16)  
Step 4: [grab] <toothbrush> (07:16 - 07:16)  
Step 5: [lookat] <toothpaste> (07:16 - 07:17)  

07:17 - 07:19, bathroom  
Step 1: [grab] <toothpaste> (07:17 - 07:17)  
Step 2: [put] <toothpaste> <toothbrush> (07:17 - 07:18)  
Step 3: [touch] <waterglass> (07:18 - 07:18)  
Step 4: [drink] <waterglass> (07:18 - 07:19)   
...

Tuesday:
...

Wednesday:
...

Thursday:
...

Friday:
...

Saturday:
...

Sunday:
...
```

# Step 4: Split Weekly Routine Scripts into Daily Files

This step converts the **weekly routine script** generated in Step 3 into **day-specific routine files**, where each file contains the routine for a single day (Monday through Sunday).

The implementation for this step is contained in the following Jupyter Notebook:

```
step_4_routine_split_by_day.ipynb
```

The workflow for this step is similar to previous steps. Open the Jupyter Notebook and run all cells from top to bottom without skipping any.

You may need to modify the **final cell**, where you can specify:

- The **weekly routine file** generated in Step 3
- The **output directory** where the per-day routine files will be saved

Each weekly routine file is split into **seven separate files**, one for each day of the week. These daily routine files are designed to support **more stable simulation**, **simpler debugging**, and **finer-grained downstream processing**.

## Purpose

The routine generation step produces a single text file that contains routines for all seven days of the week. However, many downstream tasks—such as simulation execution, sensor data generation, or per-day analysis—prefer shorter time horizons rather than long, continuous routines, as longer routines may cause the simulator to become unstable or fail.

In a later stage (**Step 9**), each daily routine file is further divided into **four or five smaller files** based on activity blocks to enable more robust and efficient processing.

## What this step does

For each weekly routine file:

1. Reads the routine file line by line.
2. Detects day headers (`Monday:` through `Sunday:`).
3. Groups all routine content under each day.
4. Writes the content for each day into a separate text file.

## Input

- A directory containing weekly routine files generated in Step 3
    
    (e.g., `{character_name}_routine_env_{#}.txt`)
    

## Output

- A new directory containing **one file per day** for each character and environment.

Each output file follows this naming format:

```
{original_filename}_{day}.txt
```

**Example:**

If the input file is:

```
Sarah_routine_env_0.txt
```

The output files will be:

```
Sarah_routine_env_0_Monday.txt
Sarah_routine_env_0_Tuesday.txt
...
Sarah_routine_env_0_Sunday.txt
```

Each file contains only the routine steps for the corresponding day. We **highly recommend keeping** this file naming format unchanged.

## Why this step is important

- Enables day-level simulation and execution, which is more stable for **the simulator** than running an entire week at once
- Simplifies sensor data generation pipelines by operating on shorter temporal segments
- Makes debugging, inspection, and validation significantly easier
- Prepares routines for further subdivision into smaller blocks in later steps (e.g., Step 9), enabling more robust downstream processing

For example, `Sarah_routine_env_0_Monday.txt` should look like the following and contain **only the routines for Monday**:

```jsx
Monday:
07:12 - 07:15, bedroom: wake_up

07:12 - 07:13, bedroom  
Step 1: [sit] <bed> (07:12 - 07:12)  
Step 2: [standup] (07:12 - 07:13)  

07:13 - 07:14, bedroom  
Step 1: [walk] <nightstand> (07:13 - 07:13)  
Step 2: [grab] <cellphone> (07:13 - 07:14)  

07:14 - 07:15, bedroom  
Step 1: [put] <cellphone> <nightstand> (07:14 - 07:14)  
Step 2: [walk] <window> (07:14 - 07:15)  
Step 3: [open] <curtains> (07:15 - 07:15)

07:15 - 07:21, bathroom: brushing_teeth

07:15 - 07:17, bathroom  
Step 1: [walk] <bathroom> (07:15 - 07:15)  
Step 2: [switchon] <lightswitch> (07:15 - 07:15)  
Step 3: [walk] <bathroomcounter> (07:15 - 07:16)   
...
```

# **Step 5: Clean and Crop Daily Routine Scripts**

This step post-processes the **per-day routine files generated in Step 4** and converts them into **simulator-ready activity blocks**.

The daily routine files produced in Step 4 retain descriptive formatting (e.g., activity names and step-based narration) intended for human readability, which is not directly compatible with VirtualHome execution. Representing routines as compact, sequential activity blocks significantly improves simulator stability and execution reliability.

In this step, each **trimmed block**, separated by a line break, corresponds to one detailed activity breakdown derived from a single *at-home activity* in **Step 2**. While **Step 3** generates the detailed breakdown for each activity, **Step 4** separates these breakdowns by day. **Step 5** further cleans and organizes the activity breakdowns into simulator-ready activity blocks, enabling more reliable downstream execution.

Step 5 addresses this by:

- Parsing each daily routine file
- Removing redundant formatting and activity names
- Cropping routines into clean, structured blocks that follow VirtualHome’s action syntax

The result is a streamlined routine file where each block represents a **continuous, simulator-ready activity sequence**.

The implementation for this step is contained in the following Jupyter Notebook:

```
step_5_clean_daily_routines.ipynb
```

The workflow for this step is similar to previous steps. Open the Jupyter Notebook and run all cells from top to bottom without skipping any.

You may need to modify the **final cell**, where you can specify:

- The input daily routine file generated in Step 4
- The output directory for cleaned, simulator-ready routine files

After this step, each cleaned routine file can be directly used for **VirtualHome simulation, block-level execution, or downstream sensor data generation**.

## Output

After running **Step 5**, each cleaned daily routine file is saved as a **simulator-ready text file** containing compact, sequential activity blocks.

### Output file naming format

```
{character_name}_routine_env_{#}_{day}_parsed.txt
```

Each file corresponds to **one character**, **one environment**, and **one day**. We **highly recommend keeping** this file naming format unchanged.

## Example

If the input daily routine file is:

```
Sarah_routine_env_0_Monday.txt
```

The cleaned, simulator-ready output file generated in Step 5 will be:

```
Sarah_routine_env_0_Monday_parsed.txt
```

For example, an activity block (with the activity name *wake_up*) in Step 4 is as follows:

```
06:42 - 06:45, bedroom: wake_up

06:42 - 06:43, bedroom  
Step 1: [standup] (06:42 - 06:42)  
Step 2: [lookat] <bed> (06:42 - 06:42)  
Step 3: [grab] <pillow> (06:42 - 06:43)  
Step 4: [put] <pillow> <bed> (06:43 - 06:43)  

06:43 - 06:45, bedroom  
Step 1: [walk] <window> (06:43 - 06:43)  
Step 2: [open] <curtains> (06:43 - 06:44)  
Step 3: [turnright] (06:44 - 06:44)  
Step 4: [walk] <doorjamb> (06:44 - 06:45)  
Step 5: [switchon] <ceilinglamp> (06:45 - 06:45)
```

After **Step 5**, the routine is transformed into the following format, where each block represents a **simulator-ready action sequence** derived from a single *at-home* activity. **Step 3** generates the detailed activity breakdown, **Step 4** organizes these breakdowns by day, and **Step 5** cleans and restructures them into compact activity blocks for reliable downstream execution.

At the beginning of each block, we prepend an additional line in the form

`[walk] <location> (start time – start time) (location)`.

This initialization step guides the agent to start in the correct location during simulation. At this stage, the original activity name (e.g., *wake_up*) is removed, and only its structured action breakdown is retained.

```jsx
[walk] <bedroom> (06:42 - 06:42) (bedroom)
[standup] (06:42 - 06:42) (bedroom)
[lookat] <bed> (06:42 - 06:42) (bedroom)
[grab] <pillow> (06:42 - 06:43) (bedroom)
[put] <pillow> <bed> (06:43 - 06:43) (bedroom)
[walk] <window> (06:43 - 06:43) (bedroom)
[open] <curtains> (06:43 - 06:44) (bedroom)
[turnright] (06:44 - 06:44) (bedroom)
[walk] <doorjamb> (06:44 - 06:45) (bedroom)
[switchon] <ceilinglamp> (06:45 - 06:45) (bedroom)
```

# Step 6: Ground Actions and Objects for VirtualHome Execution

The routines from Step 5 already have a clean block structure, but action verbs and object names may still be inconsistent (e.g., different verb forms, synonyms, or invalid object references). Step 6 resolves this by mapping each action and object to the closest valid VirtualHome primitive, ensuring that the final scripts can be executed reliably in the simulator.

Key operations in this step include:

- Extracting the **environment ID** from the filename (e.g., `env_0`)
- Mapping actions to valid VirtualHome action keys (e.g., `[grab]`, `[open]`, `[sit]`)
- Mapping objects to valid VirtualHome object keys based on **room constraints**
- Using similarity matching (via the `tools/` directory) to resolve actions and objects that do not exactly match VirtualHome primitives

The implementation for this step is contained in the following Python script:

```
step_6_action_grounding.py
```

## Environment Setup and Execution

This step relies on additional dependencies for action and object grounding.

Please create and activate a dedicated Conda environment before running the script.

### 1. Create and activate the Conda environment

```bash
conda create --name action_grounding python=3.10
conda activate action_grounding
```

### 2. Install required dependencies

```bash
pip install python-dotenv
pip install langchain-openai
pip install faiss-cpu
pip install --upgrade langchain langchain-community
```

### 3. Run the grounding script

Once the environment is set up, run the action grounding script by specifying:

- The **input file** from Step 5 (cleaned and cropped routine file)
- The **output directory** for grounded VirtualHome routines

```bash
python step_6_action_grounding.py --input_file <input_routine_file> --output_dir <output_directory>
```

**Example:**

```bash
python step_6_action_grounding.py \
  --input_file data/step_5_data/Sarah_routine_env_0_Monday_parsed.txt \
  --output_dir data/step_6_data
```

This command generates a simulator-ready routine file in the specified output directory, where all action verbs and objects are mapped to valid VirtualHome primitives based on the target environment. If certain actions or objects cannot be confidently mapped, they are left as placeholders. These unresolved entries are addressed in **Step 7**, which performs regeneration to fill in most remaining gaps and further improve execution reliability.

## Input

A **single parsed daily routine file** generated in Step 5:

```
{character_name}_routine_env_{#}_{Day}_parsed.txt
```

Example:

```
Sarah_routine_env_0_Monday_parsed.txt
```

## Output

A **grounded daily routine file** saved as:

```
{character_name}_routine_env_{#}_{Day}_parsed_grounded.txt
```

Example:

```
Sarah_routine_env_0_Monday_parsed_grounded.txt
```

We **highly recommend keeping** this file naming format unchanged.

# **Step 7: Regenerate Unresolved Actions and Objects**

Even after grounding in Step 6, some activity blocks may still contain **unresolved or placeholder entries** due to ambiguity, missing objects, or low similarity confidence. Step 7 addresses this issue by selectively **regenerating only the problematic parts** of the routine using a large language model, while preserving all correctly grounded actions.

Instead of regenerating the entire routine, this step performs **targeted regeneration**, improving accuracy and execution reliability without introducing unnecessary changes.

## Purpose

Step 7 improves simulator robustness by:

- Filling in missing or blank actions/objects
- Correcting low-confidence mappings from Step 6
- Preserving the original temporal structure and room constraints

This step significantly increases the success rate of downstream simulation and sensor generation.

## Implementation

The implementation for this step is contained in the following Jupyter Notebook:

```
step_7_regeneration.ipynb
```

The workflow for this step is similar to previous steps. Open the Jupyter Notebook and run all cells from top to bottom without skipping any. However, before running the notebook, we need to add the Conda environment set up in Step 6 to this Step 7 Jupyter Notebook, since this step still involves action verbs and object matching.

### Step-by-Step: Add a Conda Environment as a Jupyter Kernel

**1. Activate your Conda environment**

```bash
conda activate action_grounding
```

Make sure this is the environment where you installed:

- `python-dotenv`
- `langchain-openai`
- `faiss-cpu`
- `langchain`, `langchain-community`

**2. Install `ipykernel` into that environment**

This step is **required** and often forgotten.

```bash
pip install ipykernel
```

This installs the bridge between Conda and Jupyter.

**3. Register the environment as a Jupyter kernel**

```bash
python -m ipykernel install \
  --user \
  --name action_grounding \
  --display-name "Python (action_grounding)"
```

What this means:

- `-name` → internal kernel ID
- `-display-name` → what you see in Jupyter’s UI

**4. Restart Jupyter Notebook / JupyterLab**

If Jupyter was already running, **restart it**:

```bash
jupyter notebook
```

Then open your notebook.

**5. Select the kernel in Jupyter**

Inside the notebook:

- **Notebook menu** → `Kernel` → `Change Kernel`
- Select **Python (action_grounding)**

Now the notebook runs *inside that environment*.

You may need to modify the final cell to specify:

- The prompt directory used for regeneration
- The output directory for regenerated routines
- The parsed and grounded routine files to process (from Step 6)

## Output

A regenerated routine file will be saved as:

```
regenerated_{character_name}_routine_env_{#}_{Day}_parsed_grounded.txt
```

Example:

```
regenerated_Sarah_routine_env_0_Monday_parsed_grounded.txt
```

We **highly recommend keeping** this file naming format unchanged.

## Evaluation

We next evaluate how well the generated routines align with the **VirtualHome action and object specifications**.

The evaluation code performs a rule-based consistency check by comparing each generated line against the VirtualHome action grammar and environment-specific object constraints.

Specifically, the evaluation measures:

- **Action validity**: whether each action belongs to the predefined VirtualHome action set and uses the correct number of arguments.
- **Missing or unresolved actions**: lines where actions are absent or left unresolved during grounding.
- **Object completeness**: whether required objects are missing from an action.
- **Object correctness**: whether referenced objects exist in the correct room according to the environment configuration.
- **Overall error rate**: the proportion of lines containing any formatting or semantic violation.

Those statistics provide a quantitative assessment of how closely the generated text conforms to the VirtualHome library requirements, offering a clear measure of grounding quality and simulator readiness.

This evaluation script can be applied to routines generated in **Step 5, Step 6, and Step 7**, as all three stages share the same output format and differ only in the accuracy of their actions and object grounding.

Step 5 contains the raw, LLM-generated actions; Step 6 performs an initial grounding pass; and Step 7 further regenerates unresolved or incorrect lines.

On average, the error rate is around **10%** in Step 5, decreases to **8–9%** after grounding in Step 6, and is reduced to **approximately 3% or lower** after regeneration in Step 7.

The implementation for this evaluation is contained in the Jupyter Notebook:

```
evaluation.ipynb
```

Open the Jupyter Notebook and run all cells from top to bottom without skipping any. By modifying the directory path in the final cell, the notebook will automatically iterate through all routine files in the specified directory and report detailed evaluation statistics.

# Step 8: Label Generation

In this step, we classify each **activity block** produced in **Step 7** into training labels that can be used for downstream learning tasks, such as activity recognition and action prediction. The labels are drawn from five widely used datasets: **Aruba**, **Milan**, **Cairo**, **Kyoto7**, and **Orange4Home**. You may modify the code to incorporate additional datasets if needed.

For each activity block, the labels generated from all five datasets are appended to the end of every action line within the block. All lines within the same block share identical labels, reflecting the fact that they belong to the same high-level activity. The label order is **(Aruba, Milan, Cairo, Kyoto7, Orange4Home)**.

Each activity block was originally associated with an **activity name** generated in **Step 2**. In **Step 3**, these activity names were expanded into detailed routines, and in subsequent steps the routines were preserved while the activity names were removed in **Step 5**. To recover this semantic information, we jointly use the Step 4 scripts (before activity names were trimmed) together with the regenerated routines from **Step 7**. The corresponding activity name and routine block are then provided to the LLM to generate consistent labels across the five datasets.

The implementation for this step is contained in the following Jupyter Notebook:

```
step_8_label_generation.ipynb
```

The workflow for this step is similar to previous steps. Open the Jupyter Notebook and run all cells from top to bottom without skipping any.

You may need to modify the final cell to specify:

- The regenerated routine file from **Step 7**
- The corresponding routine file from **Step 4** (with activity names preserved)
- The output directory for generated label files

Ensure that the input files correspond to the same generated character, environment, and day.

## Example

If the input step 4 file is: 

```
Sarah_routine_env_0_Friday.txt
```

Then the input step 7 file should be: 

```
regenerated_Sarah_routine_env_0_Friday_parsed_grounded.txt
```

A labeled file will be saved as:

```
label_regenerated_{character_name}_routine_env_{#}_{day}_parsed_grounded.txt
```

Resulting labeled file for Sarah (env 0, Friday):

```
label_regenerated_Sarah_routine_env_0_Friday_parsed_grounded.txt
```

We **highly recommend keeping** this file naming format unchanged.

The file content should look like the following. If an activity cannot be classified into a dataset, it will be labeled as **“other.”**

```
[walk] <bedroom> (06:42 - 06:42) (bedroom) (other, master_bedroom_activity, wake, other, other)
[standup] (06:42 - 06:42) (bedroom) (other, master_bedroom_activity, wake, other, other)
[lookat] <bed> (06:42 - 06:42) (bedroom) (other, master_bedroom_activity, wake, other, other)
[grab] <pillow> (06:42 - 06:43) (bedroom) (other, master_bedroom_activity, wake, other, other)
[put] <pillow> <bed> (06:43 - 06:43) (bedroom) (other, master_bedroom_activity, wake, other, other)
[walk] <window> (06:43 - 06:43) (bedroom) (other, master_bedroom_activity, wake, other, other)
[open] <curtains> (06:43 - 06:44) (bedroom) (other, master_bedroom_activity, wake, other, other)
[turnright] (06:44 - 06:44) (bedroom) (other, master_bedroom_activity, wake, other, other)
[walk] <doorjamb> (06:44 - 06:45) (bedroom) (other, master_bedroom_activity, wake, other, other)
[switchon] <ceilinglamp> (06:45 - 06:45) (bedroom) (other, master_bedroom_activity, wake, other, other)

[walk] <bathroom> (06:45 - 06:45) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[walk] <bathroom> (06:45 - 06:45) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[switchon] <lightswitch> (06:45 - 06:45) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[walk] <bathroomcounter> (06:45 - 06:46) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[grab] <toothbrush> (06:46 - 06:46) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[lookat] <toothpaste> (06:46 - 06:47) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[grab] <toothpaste> (06:47 - 06:47) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[put] <toothpaste> <toothbrush> (06:47 - 06:48) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[drink] <waterglass> (06:48 - 06:50) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[put] <waterglass> <bathroomcounter> (06:50 - 06:50) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)
[switchoff] <lightswitch> (06:51 - 06:51) (bathroom) (bed_to_toilet, master_bathroom, other, personal_hygiene, bathroom|using_the_sink)

[walk] <bedroom> (06:51 - 06:51) (bedroom) (relax, meditate, other, other, other)
[walk] <bedroom> (06:51 - 06:51) (bedroom) (relax, meditate, other, other, other)
[switchon] <ceilinglamp> (06:51 - 06:51) (bedroom) (relax, meditate, other, other, other)
[walk] <rug> (06:51 - 06:52) (bedroom) (relax, meditate, other, other, other)
[sit] <pillow> (06:52 - 06:53) (bedroom) (relax, meditate, other, other, other)
[lookat] <window> (06:53 - 06:53) (bedroom) (relax, meditate, other, other, other)
[standup] (06:53 - 06:53) (bedroom) (relax, meditate, other, other, other)
[walk] <rug> (06:53 - 06:54) (bedroom) (relax, meditate, other, other, other)
[grab] <book> (06:54 - 06:55) (bedroom) (relax, meditate, other, other, other)
...
```

# Step 9: Block-Based Routine Splitting

In this step, we further process the labeled routines generated in **Step 8** by **splitting them into smaller, block-level files**. Each output file contains a fixed number of consecutive activity blocks (by default, four), while preserving their original order and labels.

The primary purpose of this step is to break long daily routines into shorter segments, making them more suitable for downstream tasks such as **simulator execution**. In practice, we observed that processing an entire day-long routine in the simulator is prone to failure. While we already reduced the granularity from week-level to day-level routines in **Step 4**, **Step 9 serves as the final stage of routine splitting** to ensure robustness and reliability.

The splitting is purely structural: no actions or labels are modified. All generated files remain fully aligned with the VirtualHome-compatible format and the labels produced in Step 8.

The implementation for this step is contained in the following Jupyter Notebook:

```
step_9_split_by_block.ipynb
```

The workflow for this step is similar to previous steps. Open the Jupyter Notebook and run all cells from top to bottom without skipping any.

You may need to modify the final cell to specify:

- The labeled input file generated in **Step 8**
- The output directory for the split block-level files

## Example

If the input step 8 file is: 

```
label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded.txt
```

And it includes 16 activity blocks, we are split by 4, so it will split into 4 parts:

```
part_1_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt
part_2_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bathroom.txt
part_3_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_kitchen.txt
part_4_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt
```

Please keep this file-naming format unchanged, as it will be used in later simulation steps. Each split file includes a room name to provide lightweight spatial context for the contained activity blocks. The room is automatically inferred from the routine content by extracting the most recent room annotation (e.g., `(bedroom)`, `(kitchen)`), with the first file defaulting to `bedroom` and subsequent files inheriting the last detected room.

In later simulation stages, this information becomes particularly useful because files may be processed in random order. Including the room name allows the simulator to infer the agent’s starting location for each file, enabling independent processing and flexible recombination of results.

# Step 10: Simulation

In this step, you will transfer the files generated in **Step 9** to the server so that the simulator can execute the corresponding scripts. Please refer to [**AgentSense: Server Environment Setup and Synthetic Data Generation Using the VirtualHome Simulator](https://www.notion.so/AgentSense-Server-Environment-Setup-and-Synthetic-Data-Generation-Using-the-VirtualHome-Simulator-2d6d5ba10f4080939e12ef9eff360f2d?pvs=21)** for detailed instructions on server configuration, file transfer, and synthetic data generation.

For example, if the input file for **Step 10** (generated in Step 9) is:

```
part_1_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt
```

After launching the simulator and executing the script, the following two output files (motion location file and activity-to-frame-range file) will be generated:

```
motion_part_1_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt.txt
range_part_1_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt
```

**Notes**

- The **motion location data file** contains a duplicated `.txt.txt` extension.
    
    The first `.txt` is part of the filename, while the second `.txt` is the file extension.
    
- This duplicated extension appears to be a minor issue in the simulator’s output naming and does **not** affect downstream processing.

# Step 11: Converting to Sensor Data

In this step, we will finally process the motion location data and activity-to-frame-range data to generate the actual sensor data as .npy files. 

The implementation for this step is contained in the following Jupyter Notebook:

```
step_11_generate_npy_files.ipynb
```

Open the Jupyter Notebook and run all cells from top to bottom without skipping any.

You may also need to modify the final cell to specify:

- A single folder that contains **only** the motion location data files for **one character**, on **one day**, under **one specific home environment**. These files are generated in Step 10.  For example, if you run a character named **Sarah** in **environment 0** on her **Monday** schedule, Step 9 will split the schedule into **4-5 parts**, depending on the number of activity blocks. Each part is then processed independently in Step 10, producing a **motion location file** and a corresponding **activity-to-frame-range file**. In this step, you should move **only the motion location files** associated with that character, environment, and day into the designated motion location data folder (named `step_10_motion_data` in the code). Since we will process **one character-environment-day combination at a time**. Do **not** move files for multiple characters simultaneously.
    
    Example (files that should be present in this folder for a single run):
    
    ```
    motion_part_1_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt.txt
    motion_part_2_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bathroom.txt.txt
    motion_part_3_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_kitchen.txt.txt
    motion_part_4_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt.txt
    ```
    
- **Another folder for activity-to-frame-range data files.** Similar to the motion location data folder above, this folder (named `step_10_range_data` in the code) should contain files corresponding to the **same character-environment-day combination.** For example, if you selected a character named **Sarah** in **environment 0** on her **Monday** schedule for the motion location data, this folder should include the corresponding following files:
    
    ```
    range_part_1_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt
    range_part_2_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bathroom.txt
    range_part_3_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_kitchen.txt
    range_part_4_label_regenerated_Sarah_routine_env_0_Monday_parsed_grounded_bedroom.txt
    ```
    
- **One folder for the combined files.** In Step 11, the pipeline first recombines the separately processed motion location data files from the motion folder specified above into a single motion data file, and then recombines the corresponding activity-to-frame-range data files from the range folder specified above into a single range file. The data were originally split in Step 9 and processed independently because the simulator cannot reliably handle long input files. Recombining them at this stage restores continuous motion and activity sequences for **one character, on one day, under a specific home environment**, enabling downstream processing. For example, the motion location data files and activity-to-frame-range data files for **Sarah in environment 0 on her Monday schedule** will be recombined into the two files listed below and saved in this directory (named `step_11_combined_data` in the code).
    
    ```
    combined_motion_sensors_Sarah_routine_env_0_Monday.txt
    combined_range_sensors_Sarah_routine_env_0_Monday.txt
    ```
    
- **One folder for the final `.npy` files.** After recombination, the pipeline further processes the two combined files to generate sensor data in `.npy` format, which are ready for model training. The `.npy` files should follow the structure shown below if you choose the five datasets we used (Aruba, Milan, Cairo, Kyoto7, and Orange4Home).
    
    ```
    virtual-aruba-x_time.npy
    virtual-cairo-x_time.npy
    virtual-kyoto7-x_time.npy
    virtual-milan-x_time.npy
    virtual-orange-x_time.npy
    virtual-aruba-x_sensor.npy
    virtual-cairo-x_sensor.npy
    virtual-kyoto7-x_sensor.npy
    virtual-milan-x_sensor.npy
    virtual-orange-x_sensor.npy
    virtual-aruba-x_value.npy
    virtual-cairo-x_value.npy
    virtual-kyoto7-x_value.npy
    virtual-milan-x_value.npy
    virtual-orange-x_value.npy
    virtual-aruba-y.npy
    virtual-cairo-y.npy
    virtual-kyoto7-y.npy
    virtual-milan-y.npy
    virtual-orange-y.npy
    ```