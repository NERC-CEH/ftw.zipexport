from Products.ATContentTypes.interfaces.file import IATFile
from Products.ATContentTypes.interfaces.image import IATImage
from Products.ATContentTypes.interfaces.document import IATDocument
from Products.CMFCore.interfaces import IFolderish
from ftw.zipexport.interfaces import IZipRepresentation
from ftw.zipexport.representations.general import NullZipRepresentation
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.interface import Interface
from zope.interface import implements
from StringIO import StringIO
from cgi import escape

DOC_TEMPLATE = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
    <title>%(title)s</title>
  </head>
  <body>
    <h1>%(title)s</h1>
    %(body)s
    <hr/>
    <p>
      Last modified: %(modified)s
    </p>
  </body>
</html>
"""


class PageZipRepresentation(NullZipRepresentation):
    implements(IZipRepresentation)
    adapts(IATDocument, Interface)

    def get_files(self, path_prefix=u"", recursive=True, toplevel=True):
        filename = self.context.getId()
        if not filename.endswith('.html'):
            filename += '.html'
        body = self.context.CookedBody()
        description = self.context.Description()
        if description:
            body = '<p>%s</p>\n%s' % (escape(description, quote=True), body)
        content = DOC_TEMPLATE % {
            'body': body,
            'title': escape(self.context.Title(), quote=True),
            'modified': self.context.toLocalizedTime(self.context.ModificationDate(), long_format=1),
            }

        if not isinstance(filename, unicode):
            filename = filename.decode('utf-8')

        yield (u'{0}/{1}'.format(path_prefix, filename),
               StringIO(content))


class FolderZipRepresentation(NullZipRepresentation):
    implements(IZipRepresentation)
    adapts(IFolderish, Interface)

    def get_files(self, path_prefix=u"", recursive=True, toplevel=True):
        if not recursive:
            return

        brains = self.context.getFolderContents()
        content = [brain.getObject() for brain in brains]
        if not toplevel:
            path_prefix = u'{0}/{1}'.format(path_prefix,
                                          self.context.Title().decode('utf-8'))

        for obj in content:
            adapt = getMultiAdapter((obj, self.request),
                                 interface=IZipRepresentation)

            for item in adapt.get_files(path_prefix=path_prefix,
                                    recursive=recursive,
                                    toplevel=False):
                yield item


class FileZipRepresentation(NullZipRepresentation):
    implements(IZipRepresentation)
    adapts(IATFile, Interface)

    def get_files(self, path_prefix=u"", recursive=True, toplevel=True):
        filename = self.context.getFile().getFilename()
        if not isinstance(filename, unicode):
            filename = filename.decode('utf-8')
        yield (u'{0}/{1}'.format(path_prefix, filename),
               self.get_file_open_descriptor())

    def get_file_open_descriptor(self):
        file_ = self.context.getFile()
        if hasattr(file_, 'getBlob'):
            return file_.getBlob().open()
        else:
            # For example this is the case if `self.context` is an instance
            # of `izug.ticketbox.content.attachment.TicketAttachment`.
            return StringIO(file_.data)


class ImageZipRepresentation(FileZipRepresentation):
    adapts(IATImage, Interface)
