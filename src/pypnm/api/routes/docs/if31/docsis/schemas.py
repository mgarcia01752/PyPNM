# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field

from pypnm.docsis.data_type.ClabsDocsisVersion import ClabsDocsisVersion

class DocsisBaseCapability(BaseModel):
    docsis_version:str
    clabs_docsis_version:int