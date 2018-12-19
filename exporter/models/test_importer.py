from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from collections import namedtuple
import os
import zipfile
from io import StringIO, BytesIO
import base64
import odoo

class TestExporter(models.Model):
    _name = 'testing.exporter'
    _description = "Withholding"

    name = fields.Char()
    root_folder = fields.Char()
    folders_in_root = fields.Text()
    quantity = fields.Integer()

    def zipdir(self,dirPath=None, zipFilePath=None, includeDirInZip=True):

        if not os.path.isdir(dirPath):
            raise OSError("dirPath argument must point to a directory. "
                          "'%s' does not." % dirPath)
        parentDir, dirToZip = os.path.split(dirPath)

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
            if not fileNames and not dirNames:
                outFile.writestr(zipInfo, "")
        outFile.close()

    @api.multi
    @api.model
    def test(self):
        try:
            l = '\n'.join([ self.root_folder + '/' + name for name in os.listdir(self.root_folder) if os.path.isdir(os.path.join(self.root_folder, name)) ])
            self.write({'folders_in_root': l,'name': 'done'})
        except Exception as e:
            raise UserError(e)


    @api.multi
    @api.model
    def test2(self):

        if self.folders_in_root:
            folders= str.splitlines(self.folders_in_root)
            folders_new = folders[:]
            for idx, path in enumerate(folders):
                if idx < self.quantity:
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
                        del folders_new[0]
                    except Exception as e:
                        print(e)
            self.write({'folders_in_root': '\n'.join(folders_new)})

