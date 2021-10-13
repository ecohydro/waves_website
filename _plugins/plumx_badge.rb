module Jekyll
  class RenderAltmetric < Liquid::Tag

    def initialize(tag_name, doi, tokens)
      super
      @doi = doi
    end

    def render(context)
      "<span class='altmetric-embed' data-badge-type='donut' data-doi='#{context[@doi.strip]}' data-hide-less-than='1' data-badge-popover='left'></span>"
    end
  end
end

Liquid::Template.register_tag('altmetric', Jekyll::RenderAltmetric)