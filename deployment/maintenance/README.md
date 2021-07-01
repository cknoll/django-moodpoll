# Maintenance mode


Sometimes an instance has to go offline. To keep users informed whats going on a helpful static page should be shown. This can be achieved via:


```
cp -R ~/django_project_deployment/deployment/maintenance/* ~/html/
uberspace web backend set / --apache
```

Note that the file-duplication (css, favicon etc.) is intended for robustness reasons.
