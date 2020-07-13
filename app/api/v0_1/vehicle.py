from . import bp, errors

from flask import request, jsonify, make_response

import logging
from typing import Dict, Union

from app import db
from app.models import Vehicle, Unit


@bp.route("/vehicle", methods=["GET", "POST"])
def vehicles():

    if request.method == "GET":
        return jsonify([vehicle.to_dict() for vehicle in Vehicle.query.all()])

    if request.method == "POST":
        if not request.is_json:
            raise errors.InvalidUsage(
                "Incorrect request format! Request data must be JSON"
            )

        data: Union[Dict[str, any], None] = request.get_json(silent=True)
        if not data:
            raise errors.InvalidUsage(
                "Invalid JSON received! Request data must be JSON"
            )

        if "vehicles" in data:
            vehicles = data["vehicles"]
        else:
            raise errors.InvalidUsage("'vehicles' missing in request data")

        if not vehicles:
            raise errors.InvalidUsage("'vehicles' is empty")

        params = ["capacity", "unit"]

        # Checking if each element is valid
        for vehicle in vehicles:

            check_vehicle(vehicle)

            # Filtering the dict for safety
            vehicle = {param: vehicle[param] for param in params}

        vehicle_entries = []

        # Adding vehicles to database
        for vehicle in vehicles:
            unit: Union[Unit, None] = Unit.query.filter_by(name=vehicle["unit"]).first()

            if unit is None:
                unit = Unit(name=vehicle["unit"])
                logging.debug(f"Created unit {unit}")

            vehicle_entry = Vehicle(capacity=vehicle["capacity"], unit=unit,)
            db.session.add(vehicle_entry)
            vehicle_entries.append(vehicle_entry)

        db.session.commit()

        for vehicle, vehicle_entry in zip(vehicles, vehicle_entries):
            vehicle["id"] = vehicle_entry.id

        return make_response(jsonify(vehicles), 201)


@bp.route("/vehicle/<int:id>", methods=["GET", "PUT"])
def vehicle(id: int):

    if request.method == "GET":
        return jsonify(Vehicle.query.get_or_404(id).to_dict())

    if request.method == "PUT":
        vehicle: Vehicle = Vehicle.query.get_or_404(id)
        if not request.is_json:
            raise errors.InvalidUsage(
                "Incorrect request format! Request data must be JSON"
            )
        data: Union[dict, None] = request.get_json(silent=True)
        if not data:
            raise errors.InvalidUsage(
                "Invalid JSON received! Request data must be JSON"
            )

        params = ["capacity", "unit"]

        new_vehicle: Dict[str, Union[float, str]] = {}

        for param in params:
            if param in data:
                new_vehicle[param] = data[param]
            else:
                raise errors.InvalidUsage(f"{param} missing in request data")

        # Validate vehicle
        check_vehicle(new_vehicle)

        # Update values in DB
        unit = Unit.query.filter_by(name=new_vehicle["unit"]).first()
        if unit is None:
            unit = Unit(name=new_vehicle["unit"])
            logging.debug(f"Created unit {unit}")

        vehicle.capacity = new_vehicle["capacity"]
        vehicle.unit = unit

        db.session.commit()

        return make_response(jsonify(vehicle.to_dict()), 200)


def check_vehicle(vehicle):
    params = ["capacity", "unit"]

    # Checking if all input parameters are present
    for param in params:
        if param not in vehicle:
            raise errors.InvalidUsage("Incorrect vehicle!", invalid_object=vehicle)

    if not is_float(vehicle["capacity"]) or vehicle["capacity"] < 0:
        raise errors.InvalidUsage("Invalid capacity", invalid_object=vehicle)

    if not is_string(vehicle["unit"]) or not vehicle["unit"].isalpha():
        raise errors.InvalidUsage(
            f"Invalid unit, should be string with letters only.", invalid_object=vehicle
        )


def is_float(x: any):
    return isinstance(x, float)


def is_string(x: any):
    return isinstance(x, str)
