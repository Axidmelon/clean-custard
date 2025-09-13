#!/usr/bin/env python3
"""
Example script demonstrating CSV-to-SQL functionality.

This script shows how to use the CSVToSQLConverter service to:
1. Convert CSV data to SQLite tables
2. Execute SQL queries on CSV data
3. Handle memory management

Usage:
    python examples/csv_sql_example.py
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.csv_to_sql_converter import csv_to_sql_converter

async def main():
    """Main example function."""
    print("🚀 CSV-to-SQL Converter Example")
    print("=" * 50)
    
    # Sample CSV data
    sample_csv = """name,age,salary,department,hire_date
John Doe,25,50000,Engineering,2023-01-15
Jane Smith,30,60000,Marketing,2022-11-20
Bob Johnson,35,70000,Engineering,2021-08-10
Alice Brown,28,55000,Sales,2023-03-05
Charlie Wilson,32,65000,Marketing,2022-06-18
Diana Davis,29,58000,Sales,2023-02-14
Eve Miller,31,62000,Engineering,2022-09-12
Frank Garcia,27,52000,Marketing,2023-04-08
Grace Lee,33,68000,Sales,2021-12-03
Henry Taylor,26,48000,Engineering,2023-05-20"""
    
    file_id = "example_file_1"
    
    try:
        print(f"📊 Converting CSV data to SQLite table...")
        
        # Step 1: Convert CSV to SQLite
        table_name = await csv_to_sql_converter.convert_csv_to_sql(file_id, sample_csv)
        print(f"✅ Created table: {table_name}")
        
        # Step 2: Get table schema
        print(f"\n📋 Table Schema:")
        schema = await csv_to_sql_converter.get_table_schema(file_id)
        print(f"Table: {schema['table_name']}")
        print(f"Rows: {schema['row_count']}")
        print("Columns:")
        for col in schema['columns']:
            print(f"  - {col['name']} ({col['type']})")
        
        # Step 3: Execute various SQL queries
        print(f"\n🔍 Executing SQL Queries:")
        
        queries = [
            ("Count all employees", f"SELECT COUNT(*) FROM {table_name}"),
            ("Average salary by department", f"SELECT department, AVG(salary) FROM {table_name} GROUP BY department"),
            ("Employees with salary > 60000", f"SELECT name, salary, department FROM {table_name} WHERE salary > 60000"),
            ("Top 3 highest paid employees", f"SELECT name, salary FROM {table_name} ORDER BY salary DESC LIMIT 3"),
            ("Department statistics", f"SELECT department, COUNT(*) as employee_count, AVG(salary) as avg_salary, MIN(salary) as min_salary, MAX(salary) as max_salary FROM {table_name} GROUP BY department")
        ]
        
        for description, query in queries:
            print(f"\n📝 {description}:")
            print(f"   SQL: {query}")
            
            result = await csv_to_sql_converter.execute_sql_query(file_id, query)
            
            if result["success"]:
                print(f"   ✅ Result ({result['row_count']} rows):")
                for i, row in enumerate(result["data"][:5]):  # Show first 5 rows
                    print(f"      Row {i+1}: {row}")
                if result["row_count"] > 5:
                    print(f"      ... and {result['row_count'] - 5} more rows")
            else:
                print(f"   ❌ Error: {result['error']}")
        
        # Step 4: Memory statistics
        print(f"\n💾 Memory Statistics:")
        stats = csv_to_sql_converter.get_memory_stats()
        print(f"   Active files: {stats['active_files']}")
        print(f"   Memory usage: {stats['total_memory_usage']:,} bytes")
        print(f"   Memory percentage: {stats['memory_usage_percentage']:.1f}%")
        print(f"   Memory pressure: {'Yes' if stats['memory_pressure'] else 'No'}")
        
        # Step 5: Cleanup
        print(f"\n🧹 Cleaning up...")
        await csv_to_sql_converter.cleanup_file_data(file_id)
        print(f"✅ Cleanup completed")
        
        # Final memory stats
        final_stats = csv_to_sql_converter.get_memory_stats()
        print(f"   Final active files: {final_stats['active_files']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Cleanup on error
        await csv_to_sql_converter.cleanup_file_data(file_id)
    
    print(f"\n🎉 Example completed!")

async def advanced_example():
    """Advanced example with multiple files and complex queries."""
    print("\n🚀 Advanced CSV-to-SQL Example")
    print("=" * 50)
    
    # Multiple CSV datasets
    datasets = {
        "employees": """id,name,department_id,salary
1,John Doe,1,50000
2,Jane Smith,2,60000
3,Bob Johnson,1,70000
4,Alice Brown,3,55000
5,Charlie Wilson,2,65000""",
        
        "departments": """id,name,budget
1,Engineering,1000000
2,Marketing,500000
3,Sales,750000""",
        
        "projects": """id,name,department_id,status
1,Website Redesign,2,Active
2,Mobile App,1,Completed
3,Sales Campaign,3,Active
4,Data Migration,1,Planning"""
    }
    
    try:
        # Convert all datasets
        table_names = {}
        for name, csv_data in datasets.items():
            file_id = f"advanced_{name}"
            table_name = await csv_to_sql_converter.convert_csv_to_sql(file_id, csv_data)
            table_names[name] = table_name
            print(f"✅ Created table {name}: {table_name}")
        
        # Complex queries across multiple tables
        print(f"\n🔍 Complex Multi-Table Queries:")
        
        # Note: In a real scenario, you'd need to handle joins differently
        # since each table is in a separate SQLite database
        # This example shows individual table queries
        
        queries = [
            ("Employee count by department", f"SELECT department_id, COUNT(*) FROM {table_names['employees']} GROUP BY department_id"),
            ("Department budgets", f"SELECT name, budget FROM {table_names['departments']} ORDER BY budget DESC"),
            ("Active projects", f"SELECT name, department_id FROM {table_names['projects']} WHERE status = 'Active'")
        ]
        
        for description, query in queries:
            print(f"\n📝 {description}:")
            print(f"   SQL: {query}")
            
            # Determine which file_id to use based on the table name
            if "employees" in query:
                file_id = "advanced_employees"
            elif "departments" in query:
                file_id = "advanced_departments"
            elif "projects" in query:
                file_id = "advanced_projects"
            else:
                continue
            
            result = await csv_to_sql_converter.execute_sql_query(file_id, query)
            
            if result["success"]:
                print(f"   ✅ Result ({result['row_count']} rows):")
                for row in result["data"]:
                    print(f"      {row}")
            else:
                print(f"   ❌ Error: {result['error']}")
        
        # Cleanup all files
        print(f"\n🧹 Cleaning up all files...")
        await csv_to_sql_converter.cleanup_all_data()
        print(f"✅ All cleanup completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Cleanup on error
        await csv_to_sql_converter.cleanup_all_data()

if __name__ == "__main__":
    print("CSV-to-SQL Converter Examples")
    print("This script demonstrates the CSV-to-SQL functionality.")
    print("Make sure you have the required dependencies installed.")
    print()
    
    # Run basic example
    asyncio.run(main())
    
    # Run advanced example
    asyncio.run(advanced_example())
