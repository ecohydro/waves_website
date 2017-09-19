---
layout: splash
permalink: /wsc/
title: "Water, Sustainability, and Climate"
author_profile: false
header:
  overlay_color: "#5e616c"
  overlay_image: /assets/images/cnh.jpg
excerpt: 'Exploring coupled social and environmental dynamics.<br /><br /><br /><br /><br /><br />'
tags:
    - CNH
    - WSC
    - FEW Nexus
    - Coupled Natural-Human Systems
    - Water Sustainability and Climate
    - Social-Ecological Systems
---

{% include group-by-array collection=site.posts field="tags" %}

The convergence of climate change, land use-cover change, and the rural-to-urban energy transitions are reshaping the dynamics of food, energy, and water systems across the world. In sub-Saharan Africa, these changes are exacerbated by population growth and shifting economic forces that hinder local and national governments' ability to implement integrated and sustainable resource and land governance strategies. Our efforts are focused on revealing the dynamics of production and consumption of food, energy, and water resources in sub-Saharan Africa, and using these revelations to develop solutions that can better sustain coupled food, energy, and water systems through improved multi-scale, multi-resource governance.

## News and Updates:

{% for tag in page.tags %}
    {% for post in site.posts %}
        {% if post.tags contains tag %}
            {% include archive-single.html %}
        {% endif %}
    {% endfor %}
{% endfor %}


