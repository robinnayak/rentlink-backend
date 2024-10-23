from rest_framework.renderers import JSONRenderer

class UserRenderer(JSONRenderer):
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Ensure 'data' is a dictionary before adding a status key
        if isinstance(data, dict) and 'status' not in data:
            # Add 'status' based on the response's HTTP status code
            if renderer_context['response'].status_code == 200:
                data['status'] = 'success'
            else:
                data['status'] = 'error'
        
        # Pass through the data (including non-field errors) untouched
        return super(UserRenderer, self).render(data, accepted_media_type, renderer_context)
