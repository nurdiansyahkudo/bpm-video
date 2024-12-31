/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import Fullscreen from "@website_slides/js/slides_course_fullscreen_player";
import { renderToElement } from "@web/core/utils/render";
import { jsonrpc } from "@web/core/network/rpc_service";


Fullscreen.include({
  xmlDependencies: (publicWidget.registry.websiteSlidesFullscreenPlayer.prototype.xmlDependencies || [])
    .concat(['/website_elearning_video/static/xml/extend_video_slides.xml']),

  /**
   * Extend the _renderSlide method so that slides of type "certification"
   * are also taken into account and rendered correctly
   *
   * @private
   * @override
   */
  _renderSlide: function () {
    var $this = this
    var def = this._super.apply(this, arguments);
    var slide = this.get('slide');
    var $content = this.$('.o_wslides_fs_content');
    if (slide.category === 'video' && slide.attachmentId == '' && slide.videoSourceType == "google_cloud") {
      $content.html(renderToElement('website.slides.fullscreen.video.google_cloud', { widget: slide }));
    }
    else if (slide.category === 'video' && slide.attachmentId != '' && slide.videoSourceType == undefined) {
      $content.html(renderToElement('website.slides.fullscreen.video.attachment', { widget: slide }));
    }
    if ($('.elearning_uploaded_video')[0]) {
      $('.elearning_uploaded_video').bind('contextmenu', function () { return false; });
      $('.elearning_uploaded_video')[0].addEventListener('ended', async function () {
        $this.trigger_up('slide_mark_completed', slide);
        $this.trigger_up('slide_go_next', slide);
      });
    }
    return Promise.all([def]);
  },
})

$(document).ready(function () {
  if ($('.elearning_uploaded_video')[0]) {
    $('.elearning_uploaded_video').bind('contextmenu', function () { return false; });
  }
})
