# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################
import base64
import requests
from odoo import api, fields, models, _
from logging import getLogger
from odoo.exceptions import UserError
from odoo.http import request
from werkzeug import urls
from odoo.addons.http_routing.models.ir_http import url_for
from markupsafe import Markup

_logger = getLogger(__name__)

try:
    import filetype
except ImportError:
    _logger.warning("`filetype` Python module not found. Consider installing this module.")
    filetype = None


class Slide(models.Model):
    _inherit = 'slide.slide'

    fname = fields.Char(string='Name',default='file_attachment')
    attachment = fields.Binary(string="Attachment")
    slide_attachment = fields.Many2one('ir.attachment', help="Video/Document")
    document_type = fields.Selection([('url', 'URL'), ('binary', 'File')],
                            string='Document Type', required=True, default='url', change_default=True,
                            help="You can either upload a file from your computer or copy/paste an internet link to your file.")
    google_cloud_id = fields.Char('Video Google Cloud ID', compute='_compute_google_cloud_id')
    video_source_type = fields.Selection(selection_add=[('google_cloud', 'Google Cloud')])
    slide_type = fields.Selection(selection_add=[('video','Video')])
    
    @api.onchange('attachment')
    def add_media_attachment(self):
        if self.slide_category == 'video' and not isinstance(self.attachment,bool):
            datas = self.attachment           
            vals = {
                'name': self.fname,
                'datas': datas,
                'res_model': self._name,
                'type': 'binary'  
            }
            allowed_types = self.env['website.slide.video'].get_allowed_formats()
            raw = base64.b64decode(datas)
            filetype_obj = filetype.guess(raw)
            if filetype_obj:
                mimetype = filetype_obj.mime
            else:
                mimetype = ''
            if not allowed_types.get(mimetype, False):
                raise UserError(_("Only allowed video formats can be uploaded."))

            file_size = allowed_types[mimetype] * 1024 * 1024
            given_file_size = len(base64.b64decode(datas))

            if file_size < given_file_size:
                raise UserError(_("video size less than %sMb can be uploaded and found %sMB.", allowed_types[mimetype], round(len(self.attachment)/(1024 * 1024), 2)))
            vals['mimetype'] = mimetype
            res = self.env['ir.attachment'].sudo().create(vals)
            self.slide_attachment = res.id
            
            
    @api.model
    def create(self, values):
        channel_id = self._context.get('default_channel_id')
        if channel_id:
            values['channel_id'] = channel_id
        if values.get('document_type') == 'binary':
            values['slide_category'] = 'video'
        res = super(Slide, self).create(values)
        return res

    def write(self, values):
        if values.get('document_type') == 'binary':
            values['slide_category'] = 'video'
        res = super(Slide, self).write(values)
        return res

    @api.onchange('document_type')
    def remove_link(self):
        self.url = ''
        self.binary_content = ''
        self.attachment = False
        self.image_1920 = False
        self.slide_attachment = False

    @api.onchange('url')
    def remove_attachment_link(self):
        self.slide_attachment = False

    @api.onchange('slide_category')
    def change_doc_type(self):
        if self.slide_category != 'video':
            self.document_type = 'url'

    @api.depends('slide_category', 'google_drive_id', 'video_source_type', 'youtube_id', 'google_cloud_id')
    def _compute_embed_code(self):
        super()._compute_embed_code()
        for slide in self:
            if slide.video_source_type == 'google_cloud':
                embed_code = Markup('<video class="elearning_uploaded_video" controlsList="nodownload" src="https://storage.googleapis.com/%s" controls="true" preload="metadata" allowFullScreen="true" autoplay="1" allow="autoplay" type="video/mp4" ></video>') % (slide.google_cloud_id)
                slide.embed_code = embed_code
                slide.embed_code_external = embed_code

    @api.depends('slide_category', 'source_type', 'video_source_type')
    def _compute_slide_type(self):
        super()._compute_video_source_type()
        for slide in self:
            if slide.slide_category == 'video' and slide.document_type == 'binary':
                    slide.slide_type = 'video'
                    
    def _compute_video_source_type(self):
        super()._compute_video_source_type()
        for slide in self:
            if slide.video_url:
                url_obj = urls.url_parse(slide.video_url)
                if url_obj.ascii_host == 'storage.googleapis.com':
                    slide.video_source_type = 'google_cloud'
                    slide.slide_type = 'video'

    def _fetch_external_metadata(self, image_url_only=False):
        slide_metadata, error = super()._fetch_external_metadata()
        if self.slide_category == 'video' and self.video_source_type == 'google_cloud':
            slide_metadata, error = self._fetch_google_cloud_metadata(image_url_only)
        return slide_metadata, error
    
    def _compute_google_cloud_id(self):
        for slide in self:
            if slide.video_url and slide.video_source_type == 'google_cloud':
                url_obj = urls.url_parse(slide.video_url)
                slide.google_cloud_id = url_obj.path[1:] if url_obj.path else False
            else:
                slide.google_cloud_id = False

    
    def _fetch_google_cloud_metadata(self, image_url_only=False):
        self.ensure_one()
        url_obj = urls.url_parse(self.video_url)
        error_message = False
        try:
            response = requests.get('https://storage.googleapis.com/%s' % self.google_cloud_id, timeout=3)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            _logger.warning(e)
            error_message = _('Your video could not be found on Google Cloud. Please enter valid Google Cloud URL')
        
        if error_message:
            _logger.warning('Could not fetch Google Cloud metadata: %s', error_message)
            return {}, error_message
        
        return {}, False

            

class WebsiteSlides(models.Model):
    _name = "website.slide.video"
    _description = "Website Slide Video"

    name = fields.Char("MIME Types",help="Write extension of videos allowed")
    is_active = fields.Boolean("Is Active")
    website_id = fields.Many2many("website")
    file_size = fields.Integer("Size in Mb",help='Make sure max size is allowed in your webserver(ex:-nginx) then only this limit will work.',default=15)

    def get_allowed_formats(self):
        allowed_format = {}
        website_id = self.env['website'].get_current_website()
        records = self.sudo().search([('is_active', '=', True)])
        for record in records:
            if not record.website_id or (website_id.id in record.website_id.ids):
                allowed_format.update({'video/'+record.name:record.file_size})
        return allowed_format
