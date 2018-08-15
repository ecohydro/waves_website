---
layout: splash
permalink: /environmental_sensing/
title: "Environmental Sensing"
author_profile: false
header:
  overlay_color: "#5e616c"
  overlay_image: /assets/images/environmental_sensing.jpg
excerpt: 'Improved understanding comes from detailed observation.<br /><br /><br /><br /><br /><br />'
tags:
    - Environmental Sensing
    - Arable
---

{% include group-by-array collection=site.posts field="tags" %}

New ideas and insight often require new data and observations. Sometimes those observations require the development of entirely new measurements. In other cases, the breakthrough comes from data that are collected more often, or in more places. We're taking advantage of the dramatically low costs of embedded computing and ubiquity of cellular data to extend the footprint of environmental observation. A few years ago, part of this effort was spun out of the University by [Adam Wolf]({{ site.baseurl }}{% link _people/wolf.md %}) and [Ben Siegfried]({{ site.baseurl }}{% link _people/siegfried.md %}) and now operates as [Arable Labs, Inc.](https://www.arable.com). 


## News and Updates:

{% for tag in page.tags %}
    {% for post in site.posts %}
        {% if post.tags contains tag %}
            {% include archive-single.html %}
        {% endif %}
    {% endfor %}
{% endfor %}

