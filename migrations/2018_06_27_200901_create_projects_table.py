from orator.migrations import Migration


class CreateProjectsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('projects') as table:
            table.increments('id')
            table.timestamps()
            table.string('name')
            table.string('repository_url')

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('projects')
