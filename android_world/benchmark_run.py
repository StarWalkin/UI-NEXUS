import os
from android_world.agents import infer
from android_world.agents import t3a, m3a, seeact
from android_world.env import env_launcher
from PIL import Image
import json
import argparse
import time
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--app", type=str)
# Add necessary arguments for benchmark
parser.add_argument("--task", type=str)
parser.add_argument("--lang", type=str, default="ENG")
parser.add_argument("--openai_api_model", type=str, default='gpt-4o')
parser.add_argument("--openai_api_key", type=str)
parser.add_argument("--output_dir", type=str)
parser.add_argument("--max_rounds", type=int)
parser.add_argument("--agent", type=str, choices=['T3A', 'M3A', 'SeeAct'])
parser.add_argument("--adb_path", type=str)
parser.add_argument("--device_console_port", type=int, default=0)
parser.add_argument("--device_grpc_port", type=int, default=0)
parser.add_argument("--device_serial", type=str, default=None)
parser.add_argument("--save_debug_screens", type=bool, default=False)
args = parser.parse_args()

os.environ['OPENAI_API_KEY'] = args.openai_api_key
_EMULATOR_SETUP = False

def print_and_log_error(error_message):
    print(error_message)
    error_log = [{"error_message": error_message}]
    filename = args.output_dir + "/error.json"
    # Check if the file already exists
    if not os.path.exists(filename):
        # If the file does not exist, create it and write the JSON data
        with open(filename, "w", encoding="utf-8") as logfile:
            json.dump(error_log, logfile, ensure_ascii=False)


start_time_initial = time.time()
env = env_launcher.load_and_setup_env(
    console_port=args.device_console_port,
    emulator_setup=_EMULATOR_SETUP,
    freeze_datetime=False,
    adb_path=args.adb_path,
    grpc_port=args.device_grpc_port,
    device_serial=args.device_serial
)
# Benchmark: Remove api level check
# env_launcher.verify_api_level(env)
try:
    env.reset(go_home=False)

    if args.agent == 'M3A':
        agent = m3a.M3A(env, infer.Gpt4Wrapper(args.openai_api_model))
        screenshot_key = 'benchmark_screenshot'
        grounded_action_key = 'converted_action'
        log_keys = ['action_output', 'summary']
        raw_response_key = ['action_raw_response', 'summary_raw_response']
        som_before_key = 'before_screenshot_with_som'
        som_after_key = 'after_screenshot_with_som'
    elif args.agent == 'T3A':
        agent = t3a.T3A(env, infer.Gpt4Wrapper(args.openai_api_model))
        screenshot_key = 'benchmark_screenshot'
        grounded_action_key = 'converted_action'
        log_keys = ['action_output', 'summary']
        raw_response_key = ['action_raw_response', 'summary_raw_response']
        som_before_key = None
        som_after_key = None
    elif args.agent == 'SeeAct':
        agent = seeact.SeeAct(env, model=args.openai_api_model)
        screenshot_key = 'screenshot'
        grounded_action_key = 'action'
        log_keys = ['action_gen_response', 'action_ground_response']
        raw_response_key = ['raw_action_gen_response', 'raw_action_ground_response']
        som_before_key = None
        som_after_key = None
    print('Goal: ' + args.task)

    is_done = False
    benchmark_log = []
    error_code = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    end_time_initial = time.time()
    elapsed_time_initial = end_time_initial - start_time_initial
    start_time_exec = time.time()
    for action_cnt in range(1, args.max_rounds + 1):
        try:
            response = agent.step(args.task)
        except Exception as e:
            print_and_log_error(f"Error taking step: {str(e)}")
            error_code = 2
            break
        try:
            # 如果路径不存在，则创建路径
            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir)
            # Store regular screenshot
            screenshot = Image.fromarray(response.data[screenshot_key], 'RGB')
            screenshot.save(os.path.join(args.output_dir, f'{action_cnt - 1}.png'))
            
            # Save SoM-tagged screenshots to main output directory
            if som_before_key and som_before_key in response.data:
                som_before = Image.fromarray(response.data[som_before_key], 'RGB')
                som_before.save(os.path.join(args.output_dir, f'{action_cnt - 1}_before_som.png'))
            
            if som_after_key and som_after_key in response.data:
                som_after = Image.fromarray(response.data[som_after_key], 'RGB')
                som_after.save(os.path.join(args.output_dir, f'{action_cnt - 1}_after_som.png'))
            
            # Save debug screenshots if enabled
            if args.save_debug_screens:
                # Save before SoM tagged screenshot if available
                if som_before_key and som_before_key in response.data:
                    som_before = Image.fromarray(response.data[som_before_key], 'RGB')
                    som_before.save(os.path.join(debug_dir, f'{action_cnt - 1}_before_som.png'))
                
                # Save after SoM tagged screenshot if available
                if som_after_key and som_after_key in response.data:
                    som_after = Image.fromarray(response.data[som_after_key], 'RGB')
                    som_after.save(os.path.join(debug_dir, f'{action_cnt - 1}_after_som.png'))

            action_log = [
                "",  # action type
                {
                    "detail_type": "string",  # "string" or "coordinates"
                    "detail": "",  # "Task completed." or [x, y] or f"The text \"{input_str}\" has been inputted."
                    # or f"The coordinates ({x},{y}) have been swiped to the {swipe_direction}."
                    # or f"The swipe action has been performed starting from coordinates ({start_x},{start_y}) to ({end_x},{end_y})."
                },
            ]  # second element for action details based action_type
            action_type = ''
            converted_action = response.data[grounded_action_key]
            if type(converted_action) is str:
                action_type = 'wait'
            else:
                action_type = converted_action.action_type
                if action_type == 'click':
                    action_log[1]['detail_type'] = "coordinates"
                    action_log[1]['detail'] = response.data['actual_action_coordinates']
                elif action_type == 'double_tap':
                    action_log[1]['detail_type'] = "coordinates"
                    action_log[1]['detail'] = response.data['actual_action_coordinates']
                elif action_type == 'input_text':
                    action_log[1]['detail'] = f"The text \"{response.data[grounded_action_key].text}\" has been inputted."
                elif action_type == 'keyboard_enter':
                    pass
                elif action_type == 'long_press':
                    action_log[1]['detail_type'] = "coordinates"
                    action_log[1]['detail'] = response.data['actual_action_coordinates']
                elif action_type == 'navigate_back':
                    action_log[1]["detail"] = "Back to the previous page."
                elif action_type == 'navigate_home':
                    action_log[1]["detail"] = "Return to home page."
                elif action_type == 'open_app':
                    action_log[1]['detail'] = response.data[grounded_action_key].app_name
                elif action_type == 'scroll':
                    x, y, _, _ = response.data['actual_action_coordinates']
                    action_log[1]['detail'] = f"The coordinates ({x},{y}) have been swiped to the {converted_action.direction}."
                elif action_type == 'status':
                    action_log[1]['detail'] = "Task completed."
                elif action_type == 'swipe':
                    x1, y1, x2, y2 = response.data['actual_action_coordinates']
                    action_log[1]['detail'] = f"The swipe action has been performed starting from coordinates ({x1},{y1}) to ({x2},{y2})."
                else: # ['answer', 'unknown', 'wait']
                    action_type = 'wait'
                    action_log[1]['detail'] = "No action has been taken."
            action_log[0] = action_type
            if args.agent in ['M3A', 'T3A']:
                prompt_tokens = sum([response.data[key].json()['usage']['prompt_tokens'] for key in raw_response_key if response.data[key] is not None])
                completion_tokens = sum([response.data[key].json()['usage']['completion_tokens'] for key in raw_response_key if response.data[key] is not None])
            else:
                prompt_tokens = sum([response.data[key]['usage']['prompt_tokens'] for key in raw_response_key if response.data[key] is not None])
                completion_tokens = sum([response.data[key]['usage']['completion_tokens'] for key in raw_response_key if response.data[key] is not None])
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            benchmark_log.append({
                "step": action_cnt, **{key: response.data[key] for key in log_keys},
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "action": action_log,
            })
            if response.done:
                is_done = True
                break

        except Exception as e:
            print_and_log_error(f"Error handling log: {str(e)}")
            error_code = 1
            break
finally:
    env.close()

end_time_exec = time.time()
elapsed_time_exec = end_time_exec - start_time_exec

benchmark_log.append({
    "total_steps": action_cnt - 1, "finish_signal": int(is_done),
    "elapsed_time_initial": elapsed_time_initial, "elapsed_time_exec": elapsed_time_exec,
    "total_prompt_tokens": total_prompt_tokens, "total_completion_tokens": total_completion_tokens
})

with open(args.output_dir + '/log.json', "w", encoding='utf-8') as logfile:
    json.dump(benchmark_log, logfile, ensure_ascii=False)

if error_code in [2, 3]:
    sys.exit(error_code)

if is_done:
    print("Task completed successfully")
    sys.exit(0)
elif action_cnt == args.max_rounds:
    print("Task finished due to reaching max rounds")
    sys.exit(4)
else:
    print("Task finished unexpectedly")
    sys.exit(1)
