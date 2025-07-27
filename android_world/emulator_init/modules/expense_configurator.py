"""Expense configuration for Android emulator."""

import os
import random
import time
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.task_evals.utils import sqlite_schema_utils
from android_world.task_evals.utils import sqlite_utils

from .base_configurator import BaseConfigurator


class ExpenseConfigurator(BaseConfigurator):
    """Configurator for Pro Expense app."""

    @property
    def module_name(self) -> str:
        return "Expense"

    def configure(self) -> bool:
        """Configure expense app based on configuration."""
        self._ensure_environment()

        self.log_info('Configuring Pro Expense app...')

        # Database and table information
        db_path = '/data/data/com.arduia.expense/databases/accounting.db'
        table_name = 'expense'
        app_name = 'Pro Expense'

        try:
            # Check if app is installed
            if not self._is_app_installed('com.arduia.expense'):
                self.log_warning(f"{app_name} is not installed, skipping configuration")
                return False

            # Initialize database by launching the app
            self._initialize_database(app_name)

            # Clear existing expenses if specified
            if self.config.get('clear_expenses', False):
                self._clear_expenses(db_path, table_name, app_name)

            # Add specific expenses
            expenses_to_add = self.config.get('add_expenses', [])
            if expenses_to_add:
                self._add_expenses(expenses_to_add, db_path, table_name, app_name)

            # Add random expenses if specified
            if self.config.get('add_random_expenses', False):
                random_count = self.config.get('random_expense_count', 5)
                self._add_random_expenses(random_count, db_path, table_name, app_name)

            # Relaunch app to reflect changes
            self._relaunch_app(app_name)
            self.log_info('Expense configuration completed.')
            return True

        except Exception as e:
            self.log_error(f"Failed to configure {app_name}: {e}")
            return False

    def _is_app_installed(self, package_name: str) -> bool:
        """Check if the app is installed on the device."""
        all_packages = adb_utils.get_all_package_names(self.env_controller)
        return package_name in all_packages

    def _initialize_database(self, app_name: str) -> None:
        """Launch the app to ensure database is created."""
        self.log_info(f"Initializing {app_name} database...")
        adb_utils.launch_app(app_name, self.env_controller)
        time.sleep(2)  # Wait for app to initialize
        adb_utils.close_app(app_name, self.env_controller)
        time.sleep(1)

    def _clear_expenses(self, db_path: str, table_name: str, app_name: str) -> None:
        """Clear all existing expenses."""
        self.log_info("Clearing all existing expense records...")
        sqlite_utils.delete_all_rows_from_table(table_name, db_path, self.env_controller)

    def _add_expenses(self, expenses: List[Dict[str, Any]], db_path: str, table_name: str, app_name: str) -> None:
        """Add specific expense records."""
        expense_objects = []
        for expense_data in expenses:
            try:
                # Convert amount from "35.79" to 3579
                amount_str = expense_data.get('amount', "0.0")
                amount = int(float(amount_str) * 100)

                # Create Expense object
                expense_obj = sqlite_schema_utils.Expense(
                    name=expense_data.get('name', expense_data.get('description', '')),
                    amount=amount,
                    category=expense_data.get('category', expense_data.get('category_id', 1)),
                    note=expense_data.get('note', ''),
                    created_date=expense_data.get('created_date', expense_data.get('timestamp', int(time.time() * 1000))),
                    modified_date=expense_data.get('modified_date', expense_data.get('timestamp', int(time.time() * 1000)))
                )
                expense_objects.append(expense_obj)
            except (ValueError, TypeError) as e:
                self.log_error(f"Skipping invalid expense data: {expense_data}. Error: {e}")

        if expense_objects:
            self.log_info(f"Adding {len(expense_objects)} expense records...")
            sqlite_utils.insert_rows_to_remote_db(
                expense_objects, "expense_id", table_name, db_path, app_name, self.env_controller
            )

    def _add_random_expenses(self, count: int, db_path: str, table_name: str, app_name: str) -> None:
        """Add random expense records."""
        self.log_info(f"Adding {count} random expense records...")
        expense_objects = []
        descriptions = ["Groceries", "Dinner", "Coffee", "Movie Tickets", "Gas", "Parking"]
        for _ in range(count):
            timestamp = int(time.time() * 1000) - random.randint(0, 30 * 24 * 3600 * 1000)  # within last 30 days
            expense_obj = sqlite_schema_utils.Expense(
                name=random.choice(descriptions),
                amount=random.randint(100, 10000),  # $1.00 to $100.00
                category=random.randint(1, 5),
                note='',
                created_date=timestamp,
                modified_date=timestamp
            )
            expense_objects.append(expense_obj)

        if expense_objects:
            sqlite_utils.insert_rows_to_remote_db(
                expense_objects, "expense_id", table_name, db_path, app_name, self.env_controller
            )

    def _relaunch_app(self, app_name: str) -> None:
        """Relaunch the app to refresh data."""
        self.log_info(f"Relaunching {app_name} to reflect changes...")
        adb_utils.close_app(app_name, self.env_controller)
        time.sleep(1)
        adb_utils.launch_app(app_name, self.env_controller)
        time.sleep(2) 