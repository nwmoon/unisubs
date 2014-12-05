from django.core.management.base import BaseCommand
from django.db import transaction


from videos.models import Video

class Command(BaseCommand):
    def handle(self, *args, **options):

        # to avoid locking the database for too long we do 1 query to
        # calculate which videos to update, then update them in chunks, making
        # sure to commit our transactions along the way
        CHUNK_SIZE = 25
        with transaction.commit_on_success():
            ids_to_update = (Video.objects
                             .filter(title='')
                             .values_list('id', flat=True))
        self.stdout.write("%d videos to update\n" % len(ids_to_update))
        for i in xrange(0, len(ids_to_update), 25):
            id_chunk = ids_to_update[i:i+25]
            with transaction.commit_on_success():
                for video_id in id_chunk:
                    self._update_video_title(video_id)
            self.stdout.write(".")
            self.stdout.flush()
        self.stdout.write("\n")

    def _update_video_title(self, video_id):
        try:
            v = Video.objects.get(id=video_id, title='')
        except Video.DoesNotExist:
            # video was deleted or the title got fixed
            return
        v.title = v.title_display()
        v.save()
