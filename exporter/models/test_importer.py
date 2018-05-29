# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
import datetime
import itertools
import operator
from odoo.exceptions import UserError, ValidationError
from collections import namedtuple
import os
import zipfile
from io import StringIO, BytesIO
import base64
import odoo
from os import listdir
class TestExporter(models.Model):
    _name = 'testing.exporter'
    _description = "Withholding"

    name = fields.Char()
    root_folder = fields.Char()
    folders_in_root = fields.Text()
    folder_to_export = fields.Text()

    def zipdir(self,dirPath=None, zipFilePath=None, includeDirInZip=True):
        """Create a zip archive from a directory.

        Note that this function is designed to put files in the zip archive with
        either no parent directory or just one parent directory, so it will trim any
        leading directories in the filesystem paths and not include them inside the
        zip archive paths. This is generally the case when you want to just take a
        directory and make it into a zip file that can be extracted in different
        locations.

        Keyword arguments:

        dirPath -- string path to the directory to archive. This is the only
        required argument. It can be absolute or relative, but only one or zero
        leading directories will be included in the zip archive.

        zipFilePath -- string path to the output zip file. This can be an absolute
        or relative path. If the zip file already exists, it will be updated. If
        not, it will be created. If you want to replace it from scratch, delete it
        prior to calling this function. (default is computed as dirPath + ".zip")

        includeDirInZip -- boolean indicating whether the top level directory should
        be included in the archive or omitted. (default True)

    """

        if not os.path.isdir(dirPath):
            raise OSError("dirPath argument must point to a directory. "
                          "'%s' does not." % dirPath)
        parentDir, dirToZip = os.path.split(dirPath)

        # Little nested function to prepare the proper archive path
        def trimPath(path):
            archivePath = path.replace(parentDir, "", 1)
            if parentDir:
                archivePath = archivePath.replace(os.path.sep, "", 1)
            if not includeDirInZip:
                archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
            return os.path.normcase(archivePath)

        outFile = zipfile.ZipFile(zipFilePath, "w",
                                  compression=zipfile.ZIP_DEFLATED)
        for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
            for fileName in fileNames:
                filePath = os.path.join(archiveDirPath, fileName)
                outFile.write(filePath, trimPath(filePath))
            # Make sure we get empty directories as well
            if not fileNames and not dirNames:
                zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + "/")
                # some web sites suggest doing
                # zipInfo.external_attr = 16
                # or
                # zipInfo.external_attr = 48
                # Here to allow for inserting an empty directory.  Still TBD/TODO.
                outFile.writestr(zipInfo, "")
        outFile.close()

    @api.multi
    @api.model
    def test(self):
        l = [f for f in listdir(self.root_folder)]
        str_dir= ''
        for d in l:
            str_dir = str_dir + self.root_folder + '/' +  d + "\n"

        self.write({'folders_in_root': str_dir})
        if self.folder_to_export:
            for path in str.splitlines(self.folder_to_export):
                try:
                    buff = BytesIO()
                    self.zipdir(dirPath=path, zipFilePath=buff, includeDirInZip=True)
                    self.env['ir.attachment'].create({
                        'name': '{0}.zip'.format(path.replace('/', '')),
                        'datas': base64.encodebytes(buff.getvalue()),
                        'datas_fname': '{0}.zip'.format(path.replace('/', '')),
                        'type': 'binary',
                        'res_id': self.id,
                        'res_model': self._name
                    })
                    buff.close()
                except Exception as e:
                    print(e)
