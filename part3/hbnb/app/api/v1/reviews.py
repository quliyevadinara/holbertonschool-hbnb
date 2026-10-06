from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade

api = Namespace('reviews', description='Review operations')

review_model = api.model('Review', {
    'text': fields.String(required=True, description='Text of the review'),
    'rating': fields.Integer(required=True,
                             description='Rating of the place (1-5)'),
    'user_id': fields.String(description='ID of the user '
                                         '(defaults to the logged-in user)'),
    'place_id': fields.String(required=True, description='ID of the place')
})

review_update_model = api.model('ReviewUpdate', {
    'text': fields.String(description='Text of the review'),
    'rating': fields.Integer(description='Rating of the place (1-5)')
})


def can_manage(review):
    """Authors manage their own reviews; admins manage every review."""
    return get_jwt().get('is_admin') or review.user_id == get_jwt_identity()


@api.route('/')
class ReviewList(Resource):
    @jwt_required()
    @api.expect(review_model, validate=True)
    @api.response(201, 'Review successfully created')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Unauthorized action')
    def post(self):
        """Register a new review written by the logged-in user"""
        review_data = dict(api.payload)
        current_user = get_jwt_identity()

        user_id = review_data.get('user_id', current_user)
        if user_id != current_user and not get_jwt().get('is_admin'):
            return {'error': 'Unauthorized action'}, 403
        review_data['user_id'] = user_id

        try:
            new_review = facade.create_review(review_data)
        except (ValueError, TypeError) as e:
            return {'error': str(e)}, 400
        return new_review.to_dict(), 201

    @api.response(200, 'List of reviews retrieved successfully')
    def get(self):
        """Retrieve a list of all reviews"""
        return [{'id': review.id, 'text': review.text,
                 'rating': review.rating}
                for review in facade.get_all_reviews()], 200


@api.route('/<review_id>')
class ReviewResource(Resource):
    @api.response(200, 'Review details retrieved successfully')
    @api.response(404, 'Review not found')
    def get(self, review_id):
        """Get review details by ID"""
        review = facade.get_review(review_id)
        if not review:
            return {'error': 'Review not found'}, 404
        return review.to_dict(), 200

    @jwt_required()
    @api.expect(review_update_model, validate=True)
    @api.response(200, 'Review updated successfully')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'Review not found')
    def put(self, review_id):
        """Update a review (author or admin)"""
        review = facade.get_review(review_id)
        if not review:
            return {'error': 'Review not found'}, 404
        if not can_manage(review):
            return {'error': 'Unauthorized action'}, 403
        try:
            facade.update_review(review_id, api.payload)
        except (ValueError, TypeError) as e:
            return {'error': str(e)}, 400
        return {'message': 'Review updated successfully'}, 200

    @jwt_required()
    @api.response(200, 'Review deleted successfully')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'Review not found')
    def delete(self, review_id):
        """Delete a review (author or admin)"""
        review = facade.get_review(review_id)
        if not review:
            return {'error': 'Review not found'}, 404
        if not can_manage(review):
            return {'error': 'Unauthorized action'}, 403
        facade.delete_review(review_id)
        return {'message': 'Review deleted successfully'}, 200
