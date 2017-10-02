module Jekyll
  class RenderAltmetric < Liquid::Tag

    def initialize(tag_name, doi, tokens)
      super
      @doi = doi
    end

    def render(context)
      "<div class='altmetric-embed' data-badge-type='donut' data-doi='#{context[@doi.strip]}' data-hide-less-than='5' data-badge-popover='right'></div>"
    end
  end
end

Liquid::Template.register_tag('altmetric', Jekyll::RenderAltmetric)

    