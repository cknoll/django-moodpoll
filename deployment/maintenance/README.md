# Maintenance mode


Sometimes an instance has to go offline. To keep users informed whats going on a helpful static page should be shown. This can be achieved via:


```
cp -R ~/moodpoll_deployment/deployment_helpers/maintenance/ ~/html/
uberspace web backend set / --apache
```
