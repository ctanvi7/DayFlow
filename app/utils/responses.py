from flask import jsonify


def response(success, data=None, message="", errors=None, status=200):
    return jsonify({"success": success, "data": data, "message": message, "errors": errors}), status
