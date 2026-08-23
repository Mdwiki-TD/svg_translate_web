In template_edit.html add icon to run start_job job_type=collect_templates_data
add the template title in the form with key title or titles?.

then update collect_templates_data/worker.py, in `def process(self)`

check if self.args has the form key, so we should work in that title only.

so before

```python
        # Step 1: Fetch new templates from category and add them
        self._fetch_and_add_new_templates()
```

check if self.args has a title key, and if so, `return self.process_one(self, template_title)`

```python
    def process_one(self, template_title) -> CollectTemplatesDataWorkerObject:
        """Execute the collection processing logic."""

        template: TemplateRecord = get_template_by_title(template_title)
        self.result.summary.total = 1

        self._save_progress()

        logger.info(f"Job {self.job_id}: Processing template {template.title}")

        _updated = self._process_one_item(template)
        if _updated:
            logger.info(f"Job {self.job_id}: Template {template.title} updated")

        self.finish()

        return self.result

```
