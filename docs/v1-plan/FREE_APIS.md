# V1 Free APIs & Databases Reference

**Rule:** V1 uses ONLY free APIs. No paid subscriptions, no credit cards.

---

## Access Tiers

| Tier | Description | Examples |
|------|-------------|----------|
| **Open REST** | No auth needed, just respect rate limits | Ensembl, HGNC, PDB, cBioPortal, STRING |
| **Free API Key** | Register for free, get higher rate limits | NCBI, BioGRID, OpenAlex, OMIM |
| **Free Download** | Bulk data download, no real-time API | 1000 Genomes, DepMap, WikiPathways |
| **Controlled** | Application required, free for academic | GDC/TCGA, TOPMed, MIMIC |

---

## 1. Gene Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| NCBI Gene | eutils.ncbi.nlm.nih.gov | Optional key | 3 rps / 10 with key | Gene info, sequences |
| Ensembl REST | rest.ensembl.org | None | 55K req/hr | Gene annotation, transcripts |
| HGNC | rest.genenames.org | None | Be reasonable | Official gene nomenclature |
| NCBI Clinical Tables | clinicaltables.nlm.nih.gov | None | Not published | Gene search with autocomplete |

## 2. Variant Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| ClinVar | via NCBI E-utilities | Optional key | 3 rps | Clinical variant interpretations |
| dbSNP | api.ncbi.nlm.nih.gov/variation | Optional key | 5 rps | Variant identifiers, flanking sequences |
| gnomAD | gnomad.broadinstitute.org/api | None | 10 req/60s | Population frequencies (730K+) |
| LOVD | databases.lovd.nl/shared/api | None | Not published | Gene-centered variant curation |
| UniProt Variants | ebi.ac.uk/proteins/api | None | 200 rps | Protein-level variant annotation |
| GWAS Catalog | ebi.ac.uk/gwas/rest/api | None | 15 rps | SNP-trait associations |
| cBioPortal | cbioportal.org/api | None | No limit | Cancer genomics mutations |

## 3. Expression Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| GTEx | gtexportal.org/api/v2 | None | Sequential only | Tissue expression, eQTLs |
| Expression Atlas | ebi.ac.uk/xa/api | None | Be reasonable | Cross-species differential expression |
| GEO | via NCBI E-utilities | Optional key | 3 rps | Gene expression experiments |
| Human Protein Atlas | proteinatlas.org/{id}.json | None | Not published | Protein expression in tissues |

## 4. Protein Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| UniProt | rest.uniprot.org | None | 303M req/mo | Protein sequences, annotations |
| RCSB PDB | data.rcsb.org | None | Generous | Experimental protein structures |
| AlphaFold DB | alphafold.ebi.ac.uk/api | None | Be reasonable | Predicted structures (200M+) |
| PDBe | ebi.ac.uk/pdbe/api | None | Not published | Enhanced PDB annotations |

## 5. Drug & Compound Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| ChEMBL | ebi.ac.uk/chembl | None | Generous | 2.9M compounds, bioactivity |
| PubChem | pubchem.ncbi.nlm.nih.gov | None | 5 req/sec | 110M compounds |
| DGIdb | dgidb.org/api/graphql | None | Not published | Drug-gene interactions |
| PharmGKB | api.pharmgkb.org | None | 2 rps | Pharmacogenomics |
| DrugBank | go.drugbank.com | Academic XML | Download only | Drug data (API is commercial) |

## 6. Literature Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| PubMed | via NCBI E-utilities | Optional key | 3 rps | 37M+ biomedical citations |
| Europe PMC | ebi.ac.uk/europepmc/webservices | None | Not published | 33M+ publications, full-text |
| Semantic Scholar | api.semanticscholar.org | None | 1000 rps shared | 200M+ papers, citations |
| OpenAlex | api.openalex.org | Free key | 100 rps | 500M+ works |
| Ignet | ignet.org/api/v1 | None | ~100 rps | Literature-mined gene interactions |

## 7. Pathway & Network Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| Reactome | reactome.org/ContentService | None | Generous | 2600+ curated pathways |
| KEGG | rest.kegg.jp | None | 3 rps (strict) | Pathways, modules, diseases |
| WikiPathways | wikipathways.org/json | None | Not published | Community-curated pathways |
| STRING | string-db.org/api | None | Not published | Protein interaction networks |
| BioGRID | webservice.thebiogrid.org | Free key | Not published | 3M+ interactions |
| IntAct | ebi.ac.uk/intact | None | PSICQUIC | 1.37M curated interactions |
| PSICQUIC | ebi.ac.uk/psicquic | None | PSICQUIC | Meta-service: 12+ databases |

## 8. Disease & Phenotype Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| Disease Ontology | api.disease-ontology.org | None | Not published | Disease classifications |
| Orphanet | api.orphadata.com | None | Not published | Rare disease data |
| HPO | hpo.jax.org | None | Download | Human phenotype ontology |
| OMIM | api.omim.org | Free key (academic) | Not published | Mendelian disease genes |
| ClinGen | search.clinicalgenome.org | None | Not published | Gene-disease validity |

## 9. Regulatory & Epigenomics Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| ENCODE | encodeproject.org | None | 10 rps | Regulatory elements, ChIP-seq |
| Roadmap Epigenomics | egg2.wustl.edu/roadmap | None | Download | Epigenomic maps (127 tissues) |

## 10. Single-Cell Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| CZ CELLxGENE | cellxgene.cziscience.com | None | Cloud-based | 169M+ cells, 1550+ datasets |
| Single Cell Portal | singlecell.broadinstitute.org | None | Not published | Curated scRNA-seq |

## 11. Clinical Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| ClinicalTrials.gov | clinicaltrials.gov/api/v2 | None | Not published | 470K+ clinical studies |
| MIMIC-IV | physionet.org/content/mimiciv | PhysioNet access | Via PhysioNet | ICU clinical data |

## 12. Cancer Genomics Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| cBioPortal | cbioportal.org/api | None | No limit | 300+ cancer studies |
| COSMIC | cancer.sanger.ac.uk/cosmic | Free registration | Not published | Somatic mutations in cancer |
| GDC | api.gdc.cancer.gov | Token for controlled | Not published | TCGA, TARGET data |
| DepMap | depmap.org/portal | None | Download | CRISPR essentiality scores |

## 13. Functional Genomics Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| DepMap (Sanger) | api.cellmodelpassports.sanger.ac.uk | None | Throttled | Cell model passports |
| BioGRID ORCS | orcsws.thebiogrid.org | Free key | Not published | CRISPR screen results |

## 14. Ontology Services

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| OLS (EBI) | ebi.ac.uk/ols4/api | None | Not published | 280+ ontologies search |
| BioPortal | data.bioontology.org | Free key | Not published | 700+ ontologies |
| ChEBI | ebi.ac.uk/chebi/ws | None | Not published | Chemical entities |

## 15. Microbiome Databases

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| MGnify | ebi.ac.uk/metagenomics/api | None | Not published | Metagenomic analysis |
| BV-BRC | bv-brc.org/api | Free account | Not published | Bacterial/viral genomes |

## 16. Population Genetics

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| 1000 Genomes | internationalgenome.org | None | FTP unlimited | 2504 individuals WGS |
| HGDP | via IGSR | None | FTP | 929 individuals, 54 populations |

## 17. Metabolomics

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| MetaboLights | ebi.ac.uk/metabolights | None | Not published | Metabolomics studies |
| HMDB | hmdb.ca | Academic contact | Not published | 220K+ metabolites |

## 18. Model Organisms

| Database | URL | Auth | Rate Limit | Data |
|----------|-----|------|------------|------|
| MGI (Mouse) | informatics.jax.org | None | FTP | Mouse gene annotations |
| FlyBase | flybase.org | None | REST/FTP | Drosophila genetics |
| WormBase | wormbase.org | None | REST/FTP | C. elegans genomics |
| ZFIN | zfin.org | None | REST/FTP | Zebrafish genetics |
| SGD | yeastgenome.org | None | REST/FTP | Yeast genomics |

---

## Total: 70+ Free Sources

**Connected via REST API:** 50+
**Connected via FTP/Bulk Download:** 20+
**Requires free registration:** 8 (NCBI, BioGRID, OMIM, OpenAlex, COSMIC, BioPortal, BV-BRC, DrugBank academic)

**V1 total cost: $0**
