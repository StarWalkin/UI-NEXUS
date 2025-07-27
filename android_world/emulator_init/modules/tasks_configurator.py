"""Tasks configuration for Android emulator."""

import datetime
import random
import time
import uuid
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.task_evals.utils import sqlite_schema_utils

from .base_configurator import BaseConfigurator


class TasksConfigurator(BaseConfigurator):
    """Configurator for Tasks app task management."""
    
    @property
    def module_name(self) -> str:
        return "Tasks"
    
    def configure(self) -> bool:
        """Configure tasks app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Starting configuration for Tasks app...')
        
        try:
            # Setup tasks app
            if not self._setup_tasks_app():
                return False
            
            # Clear existing tasks if specified
            if self.config.get('clear_tasks', False):
                self._clear_tasks()
            
            # Add specific tasks
            tasks_to_add = self.config.get('add_tasks', [])
            if tasks_to_add:
                added_count = self._add_specific_tasks(tasks_to_add)
                self.log_info(f"Successfully added {added_count} specified tasks")
            
            # Add random tasks if specified
            if self.config.get('add_random_tasks', False):
                random_count = self._add_random_tasks()
                self.log_info(f"Successfully added {random_count} random tasks")
            
            # Restart app to ensure changes take effect
            self._restart_tasks_app()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure tasks app: {e}")
            return False
    
    def _setup_tasks_app(self) -> bool:
        """Ensure tasks app is installed and properly configured."""
        try:
            packages = adb_utils.get_all_package_names(self.env_controller)
            if 'org.tasks' not in packages:
                self.log_error('Tasks app is not installed; cannot configure tasks')
                return False
            
            # Ensure root permissions
            adb_utils.set_root_if_needed(self.env_controller)
            
            # Launch app
            adb_utils.launch_app("tasks", self.env_controller)
            time.sleep(2)  # Wait for app to start
            
            # Return to home screen
            adb_utils.press_home_button(self.env_controller)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log_error(f"An error occurred while launching the Tasks app: {e}")
            return True  # Continue anyway
    
    def _clear_tasks(self) -> None:
        """Clear all existing tasks."""
        try:
            db_path = '/data/data/org.tasks/databases/database'
            task_table = 'tasks'
            
            self.log_info(f"Attempting to clear Tasks database table: {task_table}")
            adb_utils.execute_sql_command(db_path, f"DELETE FROM {task_table};", self.env_controller)
            self.log_info('Successfully cleared all tasks')
            
            # Verify clearing was successful
            try:
                count_cmd = ['shell', f'sqlite3 {db_path} "SELECT COUNT(*) FROM {task_table};"']
                count_response = adb_utils.issue_generic_request(count_cmd, self.env_controller)
                count_result = count_response.generic.output.decode('utf-8', errors='ignore').strip()
                self.log_info(f"Remaining tasks after clearing: {count_result}")
            except Exception as e:
                self.log_warning(f"Unable to verify clearing result: {e}")
                
        except Exception as e:
            self.log_error(f"Failed to clear tasks: {e}")
    
    def _add_specific_tasks(self, tasks_to_add: List[Dict[str, Any]]) -> int:
        """Add specific tasks from configuration."""
        db_path = '/data/data/org.tasks/databases/database'
        task_table = 'tasks'
        exclude_key = '_id'
        added_tasks = 0
        
        for task_data in tasks_to_add:
            try:
                title = task_data.get('title', '')
                if not title:
                    self.log_warning('Task title is empty; skipping')
                    continue
                
                importance = task_data.get('importance', 2)  # Default importance is medium
                
                # Handle due date
                due_date_ts = 0
                if 'due_date' in task_data:
                    due_date_ts = self._parse_date_time(
                        task_data['due_date'], 
                        task_data.get('due_time', '00:00')
                    )
                
                # Handle hide until date
                hide_until_ts = 0
                if 'hide_until_date' in task_data:
                    hide_until_ts = self._parse_date_time(
                        task_data['hide_until_date'], 
                        task_data.get('hide_until_time', '00:00')
                    )
                
                # Handle completion date
                completed_ts = 0
                if task_data.get('completed', False):
                    if 'completed_date' in task_data:
                        completed_ts = self._parse_date_time(
                            task_data['completed_date'], 
                            task_data.get('completed_time', '00:00')
                        )
                    else:
                        # If just marked as completed without date, use current time
                        completed_ts = int(datetime.datetime.now().timestamp() * 1000)
                
                # Creation and modification times default to current time or one week before due date
                created_ts = due_date_ts - 7 * 3600 * 1000 if due_date_ts > 0 else int(datetime.datetime.now().timestamp() * 1000)
                modified_ts = created_ts
                
                # Create task object
                task = sqlite_schema_utils.Task(
                    title=title,
                    importance=importance,
                    dueDate=due_date_ts,
                    hideUntil=hide_until_ts,
                    completed=completed_ts,
                    created=created_ts,
                    modified=modified_ts,
                    notes=task_data.get('notes'),
                    remoteId=str(uuid.uuid4().int),
                )
                
                # Add task to database
                self._insert_task_to_db(task, db_path, task_table, exclude_key)
                added_tasks += 1
                self.log_info(f"Successfully added task: {title}")
                
            except Exception as e:
                self.log_error(f"An error occurred while adding task '{task_data.get('title', 'Unknown')}': {e}")
        
        return added_tasks
    
    def _add_random_tasks(self) -> int:
        """Add random tasks if specified."""
        random_tasks_count = self.config.get('add_random_tasks_count', 0)
        if random_tasks_count <= 0:
            return 0
        
        db_path = '/data/data/org.tasks/databases/database'
        task_table = 'tasks'
        exclude_key = '_id'
        
        self.log_info(f"Starting to add {random_tasks_count} random tasks")
        
        # Random task titles and descriptions
        task_titles = [
            'Grocery Shopping', 'Finish Project Proposal', 'Schedule Dentist Appointment',
            'Water Plants', 'Meal Prep for the Week', 'Research Vacation Destinations',
            "Read 'The Martian'", 'Call Grandma', 'Change Air Filter',
            'Brainstorm Blog Post Ideas', "Renew Driver's License", 'Organize Closet',
            'Submit Expense Report', 'Attend Team Meeting', 'Learn to Play Guitar',
            'Reply to Emails', 'Clean Out Fridge', 'Create Budget for Next Month',
            'Back Up Computer Files', 'Take Dog to the Vet'
        ]
        
        task_descriptions = {
            'Grocery Shopping': "Don't forget milk, eggs, and bread. Also need to pick up snacks for the kids.",
            'Finish Project Proposal': "Deadline is Friday. Need to finalize budget and timeline sections.",
            'Schedule Dentist Appointment': "Teeth cleaning overdue. Call Dr. Smith's office.",
            'Water Plants': "Check moisture level before watering. Fertilize succulents.",
            'Meal Prep for the Week': "Make a grocery list based on planned meals. Cook chicken and chop veggies on Sunday.",
            'Research Vacation Destinations': "Looking for beach destinations with family-friendly activities.",
            "Read 'The Martian'": "Started last week. Aim to finish by next weekend.",
            'Call Grandma': "Catch up on family news. Ask for her famous cookie recipe.",
            'Change Air Filter': "Last changed 3 months ago. Buy a new filter at the hardware store.",
            'Brainstorm Blog Post Ideas': "Need 5 new topics for the next month's content calendar.",
            "Renew Driver's License": "Expires next month. Check DMV website for requirements.",
            'Organize Closet': "Donate old clothes and shoes. Put winter clothes in storage.",
            'Submit Expense Report': "Deadline is Wednesday. Attach receipts for all purchases.",
            'Attend Team Meeting': "Agenda includes project updates and brainstorming new initiatives.",
            'Learn to Play Guitar': "Practice chords for 30 minutes every day. Find online tutorials.",
            'Reply to Emails': "Inbox is overflowing. Prioritize urgent messages and unsubscribe from unwanted lists.",
            'Clean Out Fridge': "Check expiration dates and discard old food. Wipe down shelves.",
            'Create Budget for Next Month': "Track income and expenses. Set savings goals.",
            'Back Up Computer Files': "Use external hard drive or cloud storage. Schedule regular backups.",
            'Take Dog to the Vet': "Annual checkup and vaccinations due."
        }
        
        random_added = 0
        for _ in range(random_tasks_count):
            try:
                # Randomly select task title and description
                title = random.choice(task_titles)
                description = task_descriptions.get(title, "")
                
                # Generate random date time
                now = datetime.datetime.now()
                # Generate random due date within next 30 days
                days_ahead = random.randint(1, 30)
                hours = random.randint(9, 17)
                minutes = random.choice([0, 15, 30, 45])
                due_date = now + datetime.timedelta(days=days_ahead)
                due_date = due_date.replace(hour=hours, minute=minutes)
                due_date_ts = int(due_date.timestamp() * 1000)
                
                # 50% chance to generate hide until date, between today and due date
                hide_until_ts = 0
                if random.choice([True, False]):
                    hide_days = random.randint(0, days_ahead - 1)
                    hide_date = now + datetime.timedelta(days=hide_days)
                    hide_date = hide_date.replace(hour=hours, minute=minutes)
                    hide_until_ts = int(hide_date.timestamp() * 1000)
                
                # 30% chance to mark as completed
                completed_ts = 0
                if random.random() < 0.3:
                    completed_date = now - datetime.timedelta(days=random.randint(1, 7))
                    completed_ts = int(completed_date.timestamp() * 1000)
                
                # Random importance level
                importance = random.randint(0, 3)
                
                # Creation time one week before due date
                created_ts = due_date_ts - 7 * 24 * 3600 * 1000
                
                # Create task object
                task = sqlite_schema_utils.Task(
                    title=title,
                    importance=importance,
                    dueDate=due_date_ts,
                    hideUntil=hide_until_ts,
                    completed=completed_ts,
                    created=created_ts,
                    modified=created_ts,
                    notes=description,
                    remoteId=str(uuid.uuid4().int),
                )
                
                # Add task to database
                self._insert_task_to_db(task, db_path, task_table, exclude_key)
                random_added += 1
                
                # Log every 5 tasks added
                if random_added % 5 == 0:
                    self.log_info(f"Added {random_added} random tasks so far")
                    
            except Exception as e:
                self.log_error(f"An error occurred while adding a random task: {e}")
        
        return random_added
    
    def _parse_date_time(self, date_str: str, time_str: str = '00:00') -> int:
        """Parse date and time strings to Unix timestamp in milliseconds."""
        try:
            # Try "October 15 2023" format
            date_time = datetime.datetime.strptime(f"{date_str} {time_str}", "%B %d %Y %H:%M")
        except ValueError:
            try:
                # Try "2023-10-15" format
                date_time = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                self.log_warning(f"Unable to parse date {date_str}; using current date")
                date_time = datetime.datetime.now()
        
        return int(date_time.timestamp() * 1000)
    
    def _insert_task_to_db(self, task: sqlite_schema_utils.Task, db_path: str, task_table: str, exclude_key: str) -> None:
        """Insert task to database with proper SQL formatting."""
        # Generate SQL insert statement
        cmd, values = sqlite_schema_utils.insert_into_db(task, task_table, exclude_key)
        
        # Handle SQL with "order" keyword - use double quotes around brackets for keywords
        field_names = [field.name for field in task.__dataclass_fields__.values() if field.name != exclude_key]
        columns_list = []
        for field_name in field_names:
            if field_name == 'order':
                columns_list.append('"[order]"')
            else:
                columns_list.append(f'"{field_name}"')
        
        columns = ','.join(columns_list)
        
        # Build SQL insert statement
        bind_values = []
        for field_name in field_names:
            value = getattr(task, field_name)
            if value is None or value == 'None':
                bind_values.append('NULL')
            elif isinstance(value, str):
                # Escape single quotes in strings
                escaped_value = value.replace("'", "''")
                bind_values.append(f"'{escaped_value}'")
            else:
                bind_values.append(str(value))
        
        values_str = ','.join(bind_values)
        full_sql = f"INSERT INTO {task_table} ({columns}) VALUES ({values_str});"
        
        adb_utils.execute_sql_command(db_path, full_sql, self.env_controller)
    
    def _restart_tasks_app(self) -> None:
        """Restart tasks app to ensure changes take effect."""
        try:
            adb_utils.close_app("tasks", self.env_controller)
            time.sleep(1)
            self.log_info("Restarted the Tasks app to ensure changes take effect")
        except Exception as e:
            self.log_warning(f"An error occurred while restarting the Tasks app: {e}")
