/** @odoo-module **/

import { SlideCoursePage } from '@website_slides/js/slides_course_page';



SlideCoursePage.include({
    start: async function (parent) {
        var defs = [this._super.apply(this, arguments)];
        this.uploadPlayer = $('.elearning_uploaded_video');
        this.uploadPlayer.on('ended', this._onVideoEnded.bind(this));
        return Promise.all(defs);
    },

    _onVideoEnded: function () {
        const slide = this._getSlide($('.elearning_uploaded_video').data('id'));
        if (slide.isMember && !slide.hasQuestion && !slide.completed) {
            this.trigger_up('slide_mark_completed', slide);
        }
        if (slide.hasNext) {
            this.trigger_up('slide_go_next', slide);
        }
    },
})
