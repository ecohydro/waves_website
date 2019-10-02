module Jekyll
  class RenderDimensions < Liquid::Tag

    def initialize(tag_name, doi, tokens)
      super
      @doi = doi
    end

    def render(context)
      "<span class='__dimensions_badge_embed__' data-doi='#{context[@doi.strip]}' data-hide-zero-citations='true' data-style='small_circle'></span><script async src='https://badge.dimensions.ai/badge.js' charset='utf-8'></script>"
    end
  end
end

Liquid::Template.register_tag('dimensions', Jekyll::RenderDimensions)
