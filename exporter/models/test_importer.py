
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
    quantity = fields.Integer()

    def zipdir(self,dirPath=None, zipFilePath=None, includeDirInZip=True):
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
        l = directories=[d for d in os.listdir(self.root_folder) if os.path.isdir(d)]
        str_dir= ''
        for d in l:
            str_dir = str_dir + self.root_folder + '/' +  d + "\n"

        self.write({'folders_in_root': str_dir})


    @api.multi
    @api.model
    def test2(self):
        
        if self.folders_in_root:
            folders= str.splitlines(self.folders_in_root)
            folders_new = str.splitlines(self.folders_in_root)
            for idx, path in folders:
                if idx<= self.quantity-1:                    
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
                        del folders_new[idx]
                    except Exception as e:
                        print(e)
            self.write({'folders_in_root': '\n'.join(folders_new)})

