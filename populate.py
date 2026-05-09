import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_project.settings')
django.setup()

from operations.models import RestaurantTable

def populate_tables():
    # Clear existing tables just in case
    RestaurantTable.objects.all().delete()
    
    # Create 16 tables
    # Tables 1-4: capacity 2
    # Tables 5-12: capacity 4
    # Tables 13-16: capacity 6
    
    for i in range(1, 17):
        capacity = 4
        if i <= 4:
            capacity = 2
        elif i >= 13:
            capacity = 6
            
        RestaurantTable.objects.create(table_number=i, seating_capacity=capacity)
        
    print(f"Successfully created {RestaurantTable.objects.count()} tables.")

if __name__ == '__main__':
    populate_tables()
