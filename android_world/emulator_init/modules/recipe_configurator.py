"""Recipe configuration for Android emulator."""

import random
import time
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.task_evals.utils import sqlite_schema_utils

from .base_configurator import BaseConfigurator


class RecipeConfigurator(BaseConfigurator):
    """Configurator for recipe app (Broccoli) data."""
    
    @property
    def module_name(self) -> str:
        return "Recipe"
    
    def configure(self) -> bool:
        """Configure recipe app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring recipe settings...')
        
        try:
            # Setup recipe app
            if not self._setup_recipe_app():
                return False
            
            # Clear existing recipes if specified
            if self.config.get('clear_recipes', False):
                self._clear_recipes()
            
            # Add specific recipes
            recipes_to_add = self.config.get('add_recipes', [])
            if recipes_to_add:
                self._add_specific_recipes(recipes_to_add)
            
            # Add random recipes if specified
            if self.config.get('add_random_recipes', False):
                self._add_random_recipes()
            
            # Restart recipe app to refresh UI
            self._restart_recipe_app()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure recipe app: {e}")
            return False
    
    def _setup_recipe_app(self) -> bool:
        """Ensure recipe app is installed and properly configured."""
        try:
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if 'com.flauschcode.broccoli' not in all_packages:
                self.log_error("Broccoli Recipe app is not installed! Please install it first.")
                return False
            
            # Ensure root permissions
            adb_utils.set_root_if_needed(self.env_controller)
            
            # Launch app
            adb_utils.launch_app("broccoli app", self.env_controller)
            time.sleep(2)  # Wait for app to start
            
            # Return to home screen
            adb_utils.press_home_button(self.env_controller)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log_error(f"An error occurred while launching the recipe app or setting permissions: {e}")
            return True  # Continue anyway
    
    def _clear_recipes(self) -> None:
        """Clear all existing recipes."""
        try:
            db_path = '/data/data/com.flauschcode.broccoli/databases/broccoli'
            table_name = 'recipes'
            
            self.log_info(f"Attempting to clear the Recipe database table: {table_name}")
            adb_utils.execute_sql_command(db_path, f"DELETE FROM {table_name};", self.env_controller)
            self.log_info('Successfully cleared all recipes')
            
            # Verify clearing was successful
            try:
                count_cmd = ['shell', f'sqlite3 {db_path} "SELECT COUNT(*) FROM {table_name};"']
                count_response = adb_utils.issue_generic_request(count_cmd, self.env_controller)
                count_result = count_response.generic.output.decode('utf-8', errors='ignore').strip()
                self.log_info(f"Number of recipes remaining after clearing: {count_result}")
            except Exception as e:
                self.log_warning(f"Unable to verify clearing result: {e}")
                
        except Exception as e:
            self.log_error(f"Failed to clear recipes: {e}")
    
    def _add_specific_recipes(self, recipes_to_add: List[Dict[str, Any]]) -> None:
        """Add specific recipes from configuration."""
        db_path = '/data/data/com.flauschcode.broccoli/databases/broccoli'
        table_name = 'recipes'
        added_recipes = 0
        
        for recipe_data in recipes_to_add:
            try:
                # Create Recipe object from configuration
                recipe = sqlite_schema_utils.Recipe(
                    title=recipe_data.get('title', ''),
                    description=recipe_data.get('description', ''),
                    servings=recipe_data.get('servings', ''),
                    preparationTime=recipe_data.get('preparationTime', ''),
                    source=recipe_data.get('source', ''),
                    ingredients=recipe_data.get('ingredients', ''),
                    directions=recipe_data.get('directions', ''),
                    favorite=recipe_data.get('favorite', 0)
                )
                
                # Generate SQL insert statement and parameters
                insert_sql, values = sqlite_schema_utils.insert_into_db(
                    recipe, table_name, exclude_key='recipeId'
                )
                
                # Format SQL with values (since execute_sql_command doesn't accept parameters)
                formatted_sql = self._format_sql_with_values(insert_sql, values)
                
                # Execute SQL insert
                adb_utils.execute_sql_command(
                    db_path, 
                    f"{formatted_sql};", 
                    self.env_controller
                )
                
                self.log_info(f"Successfully added recipe: {recipe.title}")
                added_recipes += 1
                
            except Exception as e:
                self.log_error(f"Failed to add recipe '{recipe_data.get('title', 'Unknown')}': {e}")
        
        self.log_info(f"Successfully added {added_recipes} recipes")
    
    def _add_random_recipes(self) -> None:
        """Add random recipes if specified."""
        num_random_recipes = self.config.get('random_recipe_count', 5)
        db_path = '/data/data/com.flauschcode.broccoli/databases/broccoli'
        table_name = 'recipes'
        random_recipes_added = 0
        
        # Predefined recipes list
        predefined_recipes = [
            {'title': 'Spicy Tuna Wraps', 'directions': 'Mix canned tuna with mayo and sriracha. Spread on tortillas, add lettuce and cucumber slices, roll up.'},
            {'title': 'Avocado Toast with Egg', 'directions': 'Toast bread, top with mashed avocado, a fried egg, salt, pepper, and chili flakes.'},
            {'title': 'Greek Salad Pita Pockets', 'directions': 'Fill pita pockets with lettuce, cucumber, tomato, feta, olives, and Greek dressing.'},
            {'title': 'Quick Fried Rice', 'directions': 'Sauté cooked rice with vegetables, add soy sauce and scrambled eggs. Toss until hot.'},
            {'title': 'Pesto Pasta with Peas', 'directions': 'Cook pasta, stir in pesto sauce and cooked peas. Add Parmesan cheese before serving.'},
            {'title': 'BBQ Chicken Quesadillas', 'directions': 'Mix shredded cooked chicken with BBQ sauce. Place on tortillas with cheese, fold and cook until crispy.'},
            {'title': 'Tomato Basil Bruschetta', 'directions': 'Top sliced baguette with a mix of chopped tomatoes, basil, garlic, olive oil, salt, and pepper.'},
            {'title': 'Lemon Garlic Tilapia', 'directions': 'Sauté tilapia in butter, add lemon juice and garlic. Serve with steamed vegetables.'}
        ]
        
        # Optional descriptions
        descriptions = [
            'A quick and easy meal, perfect for busy weekdays.',
            'A delicious and healthy choice for any time of the day.',
            'An ideal recipe for experimenting with different flavors and ingredients.'
        ]
        
        # Optional servings
        servings_options = [
            '1 serving', '2 servings', '3-4 servings', '6 servings', '8 servings'
        ]
        
        # Optional preparation times
        prep_time_options = [
            '10 mins', '20 mins', '30 mins', '45 mins', '1 hrs', '2 hrs'
        ]
        
        # Add random recipes
        for i in range(num_random_recipes):
            try:
                # Randomly select a predefined recipe
                recipe_template = random.choice(predefined_recipes)
                
                # Create recipe with random attributes
                recipe = sqlite_schema_utils.Recipe(
                    title=recipe_template['title'],
                    description=random.choice(descriptions),
                    servings=random.choice(servings_options),
                    preparationTime=random.choice(prep_time_options),
                    directions=recipe_template['directions'],
                    ingredients='varies',
                    favorite=random.choice([0, 1])
                )
                
                # Generate SQL insert statement and parameters
                insert_sql, values = sqlite_schema_utils.insert_into_db(
                    recipe, table_name, exclude_key='recipeId'
                )
                
                # Format SQL with values
                formatted_sql = self._format_sql_with_values(insert_sql, values)
                
                # Execute SQL insert
                adb_utils.execute_sql_command(
                    db_path, 
                    f"{formatted_sql};", 
                    self.env_controller
                )
                
                self.log_info(f"Successfully added random recipe #{i+1}: {recipe.title}")
                random_recipes_added += 1
                
            except Exception as e:
                self.log_error(f"Failed to add random recipe #{i+1}: {e}")
        
        self.log_info(f"Successfully added {random_recipes_added} random recipes")
    
    def _format_sql_with_values(self, insert_sql: str, values: List[Any]) -> str:
        """Format SQL statement with values to replace placeholders."""
        formatted_sql = insert_sql
        for value in values:
            if value is None:
                formatted_sql = formatted_sql.replace('?', 'NULL', 1)
            elif isinstance(value, str):
                # Properly handle single quotes in strings to avoid SQL injection
                sanitized_value = value.replace("'", "''")
                formatted_sql = formatted_sql.replace('?', f"'{sanitized_value}'", 1)
            elif isinstance(value, int):
                formatted_sql = formatted_sql.replace('?', str(value), 1)
            else:
                formatted_sql = formatted_sql.replace('?', str(value), 1)
        return formatted_sql
    
    def _restart_recipe_app(self) -> None:
        """Restart recipe app to refresh UI."""
        try:
            adb_utils.launch_app("broccoli app", self.env_controller)
            self.log_info("Broccoli app restarted to refresh the UI")
        except Exception as e:
            self.log_warning(f"Failed to restart the Broccoli app: {e}")
