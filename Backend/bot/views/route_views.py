import json
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

SECTOR_COORDS = {
    "PUERTA MARAVEN": (11.696, -70.183),
    "COMUNIDAD CARDÓN": (11.668, -70.199),
    "MARAVEN": (11.670, -70.190),
    "CENTRO DE PUNTO FIJO": (11.705, -70.207),
    "BANCO OBRERO": (11.710, -70.198),
    "CAJA DE AGUA": (11.720, -70.195),
    "SANTA IRENE": (11.700, -70.195),
    "SANTA FE": (11.708, -70.188),
    "LAS MARGARITAS": (11.725, -70.180),
    "JUDIBANA": (11.758, -70.190),
    "LOS TAQUES": (11.833, -70.250),
    "VILLA MARINA": (11.850, -70.233),
    "EL CAYUDE": (11.600, -70.000),
}

RESTAURANT_LOCATION = (11.670464, -70.151655)


@csrf_exempt
def calculate_route_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        location_input = data.get("location", "").strip().upper()

        user_coords = SECTOR_COORDS.get(location_input)
        if not user_coords:
            try:
                parts = location_input.split(',')
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    user_coords = (lat, lon)
            except Exception:
                pass

        if not user_coords:
            return JsonResponse({"error": "Ubicación no reconocida o inválida"}, status=400)

        from bot_Cliente.dijkstra import PathFinder

        finder = PathFinder()
        if not finder.loaded:
            map_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "bot_Cliente",
                "map.osm",
            )
            finder.load_map(map_path)

        result = finder.find_path(RESTAURANT_LOCATION, user_coords)
        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Error calculating route: {e}")
        return JsonResponse({"error": str(e)}, status=500)
