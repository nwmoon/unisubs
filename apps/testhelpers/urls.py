from django.conf.urls import  patterns, url

urlpatterns = patterns('testhelpers.views',
    url(r'echo-json/$', "echo_json", name="echo-json"),
    url(r'^load-teams-fixture/$', 'load_team_fixtures', name='load_team_fixture'),

)
