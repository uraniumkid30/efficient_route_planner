# Fuel Route Planner Architecture

## Overview

This document explains the architecture of the Fuel Route Planner system for beginners. Think of it as building a smart GPS that not only tells you where to go but also where to buy cheap gas along the way.

## The Problem We're Solving

Imagine you're driving from New York to Los Angeles. Your truck:
- Gets 10 miles per gallon
- Has a 500-mile range
- Needs to find the cheapest gas stations along the route

The challenge: Gas prices vary by location, and some stations might require small detours. How do you find the optimal combination of stops to minimize total fuel cost?

## System Architecture
 Client 
 (API Consumer) 

 Django REST API 

 Views │ │ Serializers │ │ Documentation │ 
 (Endpoints) │ │ (Validation)│ │ (drf-spectacular)│ 

Route Processor Service 

 Cache Service  Fuel Station Repository │ 
 (Redis) │ │ (Data Access) │

│

 Routing │ │ Planner │ │Fuel Optimizer │
 (OSRM API) │ │ (Projection) │ │ (Algorithm) │

│ 


 Get route │ │ Find nearby │ │ Calculate best│
 coordinates │ │ stations │ │ fuel stops 

│


 Map View 
(Folium) 

text

##  Component Breakdown (Explained Simply)

### 1. **Views** (`views.py`)
**What it does**: Like a restaurant host - receives customer requests and seats them.

**Analogy**: When you call a restaurant, the host:
- Takes your name (validates input)
- Finds a table (calls the processor)
- Brings you to your seat (returns response)

**Code example**:
```
python
class RoutePlannerView(APIView):
    def post(self, request):
        # 1. Check if request is valid
        serializer = RouteRequestSerializer(data=request.data)
        
        # 2. Call the kitchen (processor)
        result = self.service.execute(route_request)
        
        # 3. Serve the meal (return response)
        return Response(result)
```
2. Serializers (serializers.py)
What it does: Like a bouncer at a club - checks IDs and ensures data is valid.

Analogy:

"Is this a valid coordinate?" (format check)

"Is this in the USA?" (region validation)

"Does this make sense?" (business rules)

3. Route Processor (processor.py)
What it does: Like a project manager - coordinates all the other components.

Responsibilities:

Gets the route from OSRM

Finds gas stations along the route

Calculates optimal fuel stops

Generates the map

Caches results for speed

4. Planner (planner.py)
What it does: Like a GPS - finds which stations are near your route.

Key Challenge: How do we find stations near a curvy line, not just a straight line?

Solution:

Convert latitude/longitude to 3D coordinates (think of Earth as a sphere)

Use a KD-tree (like a filing cabinet organized by location)

Find the closest point on the route for each station.

I couldnt fully implement the Kd-tree so i used the haversine

5. Fuel Optimizer (fuel_optimizer.py)
What it does: Like a financial advisor - decides when and where to buy fuel.

The Decision Problem:

Buy now at $3.50/gal, or wait for $3.30/gal 200 miles ahead?

Is the 5-mile detour worth it for cheaper gas?

How much should I buy?

Algorithm (Greedy Approach):

text
At each station:
1. Can I reach it with current fuel?
2. Look ahead at stations within range
3. If I see a cheaper station:
   - Buy just enough to reach it
4. If no cheaper station ahead:
   - Fill the tank
6. Map View (map_view.py)
What it does: Like a visual dashboard - shows the route and stops on a map.

Features:

Blue line = main route

Orange markers = fuel stops

Dotted orange lines = detour paths

Green flag = start, Red flag = end

## Data Flow (Step by Step)
Let's trace a request from start to finish:


Step 1: Client sends request

 POST /plan  
 start: "40.7128, -74.0060"  
 end: "41.8781, -87.6298"    

Step 2: Validate coordinates

 RouteRequestSerializer 
 Valid format      
 Within USA        
 Both coordinates  
       
       
Step 3: Check cache
 Cache Service       
 Has this route been
 calculated before? 
       
Step 4: Get route from OSRM
 OSRM API           
 GET /route/v1/... 
 Returns:           
 Path coordinates
 Distance        

Step 5: Find stations
 Planner Component   
 1. Load station DB 
 2. Filter by bbox  
 3. KD-tree lookup  
 4. Calculate detour

       
Step 6: Optimize fuel stops
 Fuel Optimizer      
1. Start with full 
2. At each station:
    - Check range   
    - Look ahead    
    - Decide amount 


Step 7: Generate map
 Map View           
 1. Center map     
 2. Draw route     
 3. Add markers    
 4. Save HTML file 

Step 8: Return response
 JSON Response      
 Distance: 2794mi 
 4 fuel stops    
 Total cost: $845
 Map URL         

## Caching Strategy
Why cache?

OSRM API calls are slow and rate-limited

Routes between same cities don't change

How it works:

text
Cache Key = hash(start + finish + station_version)
                    ↓
              Redis/Memory
                    ↓
           TTL: 60 hours (adjustable)
Cache invalidation:

When fuel prices update (via CSV reload)

When algorithm version changes

## Algorithms Explained
1. Haversine Formula
Purpose: Calculate distance between two points on a sphere

Why not straight line? Earth is round!


2. KD-Tree Nearest Neighbor
Purpose: Find closest route point to a station

Time Complexity: O(log n) instead of O(n)

Analogy: Instead of checking every point on a 3000-mile route, it's like having a phonebook organized by location.

3. Greedy Fuel Optimization
Purpose: Minimize cost with future knowledge

Why greedy? The optimal solution at each local decision leads to global optimum because fuel is a consumable resource with no backward travel.

## Configuration & Settings
python
# Key configuration parameters
MAX_RANGE = 500        # miles
MPG = 10              # miles per gallon
MAX_DETOUR_MILES = 10 # reasonable detour limit
CORRIDOR_MILES = 50   # initial search radius

## Performance Considerations
Bottlenecks:

OSRM API call - mitigated by caching

Station projection - O(n*m) optimized with KD-tree

Map generation - happens once per route

Optimizations implemented:

Bounding box pre-filtering

Vectorized numpy operations

Batch processing for large station sets

Result caching

## Testing Strategy
Unit Tests: Test individual components in isolation

"Does the haversine formula return correct distances?"

"Does the fuel optimizer choose the right station?"

Integration Tests: Test components working together

"Can we get a route and find stations?"

End-to-End Tests: Test complete API

"Does a real request return expected results?"

# Learning Resources
For beginners wanting to understand each concept:

Django REST Framework:

Official Tutorial

Geospatial Concepts:

Haversine Formula Explained

KD-Tree Visualization

Optimization Algorithms:

Greedy Algorithms

Dynamic Programming vs Greedy

Caching:

Redis in Django

Cache-Aside Pattern

This architecture document is designed to be understood by developers at all levels. Each component is explained with real-world analogies and visual representations.