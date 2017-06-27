{% if pull.builds %}
{% set build = pull.builds | sort(attribute='number', reverse=True) | first %}
# Build {{ build.status.name }}

Started: {{ build.started_at }}
Finished: {{ build.finished_at }}

<table>
  <tr>
    <th>Product</th>
    <th>Status</th>
    <th>Allowed Failure</th>
    <th>Links</th>
  </tr>
  {% for job in build.jobs|sort(attribute='id') %}
  <tr>
    <td>{{ job.product.name|replace(':', ' ')|title }}</td>
    <td>{{ job.state.name|capitalize }}</td>
    <td>{{ 'Yes' if job.allow_failure else 'No' }}</td>
    <td>
      <a href="http://45.55.181.25/job/{{job.number}}">Dashboard</a> |
      <a href="https://travis-ci.org/bobholt/web-platform-tests/jobs/{{job.id}}">TravisCI</a></td>
  </tr>
  {% endfor %}
</table>

View more information about this build on:

- [WPT Results Dashboard](http://45.55.181.25/build/{{build.number}})
- [TravisCI](https://travis-ci.org/bobholt/web-platform-tests/builds/{{build.id}})

{% else %}
# Build Status

No builds to show.
{% endif %}

