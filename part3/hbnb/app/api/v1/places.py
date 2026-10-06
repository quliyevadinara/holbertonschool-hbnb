from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade

api = Namespace('places', description='Place operations')

# Related entities, used to document the nested place details
amenity_model = api.model('PlaceAmenity', {
    'id': fields.String(description='Amenity ID'),
    'name': fields.String(description='Name of the amenity')
})

user_model = api.model('PlaceUser', {
    'id': fields.String(description='User ID'),
    'first_name': fields.String(description='First name of the owner'),
    'last_name': fields.String(description='Last name of the owner'),
    'email': fields.String(description='Email of the owner')
})

review_model = api.model('PlaceReview', {
    'id': fields.String(description='Review ID'),
    'text': fields.String(description='Text of the review'),
    'rating': fields.Integer(description='Rating of the place (1-5)'),
    'user_id': fields.String(description='ID of the user')
})

place_model = api.model('Place', {
    'title': fields.String(required=True, description='Title of the place'),
    'description': fields.String(description='Description of the place'),
    'price': fields.Float(required=True, description='Price per night'),
    'latitude': fields.Float(required=True,
                             description='Latitude of the place'),
    'longitude': fields.Float(required=True,
                              description='Longitude of the place'),
    'owner_id': fields.String(description='ID of the owner '
                                          '(defaults to the logged-in user)'),
    'amenities': fields.List(fields.String,
                             description="List of amenities ID's")
})

place_update_model = api.model('PlaceUpdate', {
    'title': fields.String(description='Title of the place'),
    'description': fields.String(description='Description of the place'),
    'price': fields.Float(description='Price per night'),
    'latitude': fields.Float(description='Latitude of the place'),
    'longitude': fields.Float(description='Longitude of the place'),
    'owner_id': fields.String(description='ID of the owner (admin only)'),
    'amenities': fields.List(fields.String,
                             description="List of amenities ID's")
})


def place_details(place):
    """Full place representation, including its related objects."""
    data = place.to_dict()
    del data['owner_id']
    data['owner'] = place.owner.to_dict()
    data['amenities'] = [{'id': amenity.id, 'name': amenity.name}
                         for amenity in place.amenities]
    data['reviews'] = [{'id': review.id, 'text': review.text,
                        'rating': review.rating, 'user_id': review.user.id,
                        'user_name': f"{review.user.first_name} "
                                     f"{review.user.last_name}"}
                       for review in place.reviews]
    return data


def can_manage(place):
    """Owners manage their own places; admins manage every place."""
    return get_jwt().get('is_admin') or place.owner_id == get_jwt_identity()


@api.route('/')
class PlaceList(Resource):
    @jwt_required()
    @api.expect(place_model, validate=True)
    @api.response(201, 'Place successfully created')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Unauthorized action')
    def post(self):
        """Register a new place owned by the logged-in user"""
        place_data = dict(api.payload)
        current_user = get_jwt_identity()

        owner_id = place_data.get('owner_id', current_user)
        if owner_id != current_user and not get_jwt().get('is_admin'):
            return {'error': 'Unauthorized action'}, 403
        place_data['owner_id'] = owner_id

        try:
            new_place = facade.create_place(place_data)
        except (ValueError, TypeError) as e:
            return {'error': str(e)}, 400
        return new_place.to_dict(), 201

    @api.response(200, 'List of places retrieved successfully')
    def get(self):
        """Retrieve a list of all places"""
        return [{'id': place.id, 'title': place.title, 'price': place.price,
                 'latitude': place.latitude, 'longitude': place.longitude}
                for place in facade.get_all_places()], 200


@api.route('/<place_id>')
class PlaceResource(Resource):
    @api.response(200, 'Place details retrieved successfully')
    @api.response(404, 'Place not found')
    def get(self, place_id):
        """Get place details by ID"""
        place = facade.get_place(place_id)
        if not place:
            return {'error': 'Place not found'}, 404
        return place_details(place), 200

    @jwt_required()
    @api.expect(place_update_model, validate=True)
    @api.response(200, 'Place updated successfully')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'Place not found')
    def put(self, place_id):
        """Update a place (owner or admin)"""
        place = facade.get_place(place_id)
        if not place:
            return {'error': 'Place not found'}, 404
        if not can_manage(place):
            return {'error': 'Unauthorized action'}, 403

        place_data = api.payload
        if (place_data.get('owner_id', place.owner_id) != place.owner_id
                and not get_jwt().get('is_admin')):
            return {'error': 'Unauthorized action'}, 403

        try:
            facade.update_place(place_id, place_data)
        except (ValueError, TypeError) as e:
            return {'error': str(e)}, 400
        return {'message': 'Place updated successfully'}, 200

    @jwt_required()
    @api.response(200, 'Place deleted successfully')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'Place not found')
    def delete(self, place_id):
        """Delete a place and its reviews (owner or admin)"""
        place = facade.get_place(place_id)
        if not place:
            return {'error': 'Place not found'}, 404
        if not can_manage(place):
            return {'error': 'Unauthorized action'}, 403
        facade.delete_place(place_id)
        return {'message': 'Place deleted successfully'}, 200


@api.route('/<place_id>/reviews')
class PlaceReviewList(Resource):
    @api.response(200, 'List of reviews for the place retrieved successfully')
    @api.response(404, 'Place not found')
    def get(self, place_id):
        """Get all reviews for a specific place"""
        reviews = facade.get_reviews_by_place(place_id)
        if reviews is None:
            return {'error': 'Place not found'}, 404
        return [{'id': review.id, 'text': review.text,
                 'rating': review.rating} for review in reviews], 200
