# GenomeAI - Comprehensive Free Public APIs Reference

> Last updated: August 2026
> Purpose: Inform GenomeAI product direction for biomedical/genomic data integration

---

## 1. GENOMIC DATABASES

### 1.1 NCBI/Entrez E-utilities
- **URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- **Data**: 38 databases: PubMed, Gene, Nucleotide, Protein, PMC, ClinVar, dbSNP, BioProject, BioSample, SRA, etc.
- **Auth**: Free API key (recommended). Without key: 3 req/sec. With key: 10 req/sec (higher by request).
- **Format**: XML, JSON (via retmode=json)
- **Key endpoints**: `esearch.fcgi`, `efetch.fcgi`, `esummary.fcgi`, `elink.fcgi`, `einfo.fcgi`
- **GenomeAI value**: Central hub for ALL biomedical data. Gene lookups, sequence retrieval, literature search, cross-database linking. **Must-have integration.**

### 1.2 Ensembl REST API
- **URL**: `https://rest.ensembl.org`
- **Data**: Genome annotation, gene models, variants, sequences, cross-references, regulatory features, alignments, taxonomies
- **Auth**: None required. No API key.
- **Rate limits**: 55,000 requests/hour (~15 req/sec self-throttle recommended)
- **Format**: JSON
- **Key endpoints**: `/sequence/id/{id}`, `/variation/homo_sapiens/{id}`, `/overlap/region/{species}:{region}`, `/xref/symbol/{species}/{symbol}`
- **GenomeAI value**: Primary source for genome annotation and gene-level data across species. **Must-have integration.**

### 1.3 UCSC Genome Browser REST API
- **URL**: `https://api.genome.ucsc.edu`
- **Data**: Genome assemblies, DNA sequences, annotation tracks, track hubs for hundreds of organisms
- **Auth**: None required
- **Rate limits**: 1 req/sec recommended
- **Format**: JSON
- **Key endpoints**: `/getData/sequence`, `/getData/track`, `/list/tracks`, `/list/ucscGenomes`, `/search`
- **GenomeAI value**: Genome sequence extraction, track data retrieval, assembly info. **High-value for variant context.**

### 1.4 gnomAD GraphQL API
- **URL**: `https://gnomad.broadinstitute.org/api`
- **Data**: Population allele frequencies, variant annotations, constraint scores, pLI scores across 730K+ individuals (v4)
- **Auth**: None required
- **Rate limits**: ~1 req/sec recommended (no published hard limit, aggressive throttling enforced)
- **Format**: GraphQL (POST with query body)
- **Datasets**: gnomad_r4 (GRCh38 exomes), gnomad_r4_genomes, gnomad_r3, gnomad_r2_1 (GRCh37)
- **GenomeAI value**: Essential for variant pathogenicity assessment via allele frequency. **Must-have for clinical genomics.**

### 1.5 ClinVar (via E-utilities + Variation Services)
- **URLs**:
  - E-utilities: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` (db=clinvar)
  - Variation Services: `https://api.ncbi.nlm.nih.gov/variation/v0`
  - Clinical Tables API: `https://clinicaltables.nlm.nih.gov/api/variants/v4/search`
- **Data**: Clinical significance of variants, disease-variant relationships, review status, assertions
- **Auth**: None (via E-utilities with NCBI API key for higher rates)
- **Format**: XML, JSON, VCF
- **GenomeAI value**: Core clinical variant interpretation. **Must-have.**

### 1.6 dbSNP (via Variation Services)
- **URL**: `https://api.ncbi.nlm.nih.gov/variation/v0/`
- **Data**: 2B+ variant submissions, RefSNP clusters, allele frequencies, population data, molecular consequence
- **Auth**: None required
- **Format**: JSON (SPDI model)
- **Key endpoints**: `/beta/refsnp/{rsid}`, `/hgvs/{hgvs}/contextuals`, `/spdi/{spdi}/rsids`, VCF annotation via POST
- **GenomeAI value**: Variant identification and annotation. **Must-have.**

---

## 2. DRUG/PHARMACEUTICAL

### 2.1 OpenFDA
- **URL**: `https://api.fda.gov`
- **Data**: Drug adverse events (FAERS), drug labeling (SPL), NDC directory, drug recalls, drug approvals, drug shortages
- **Auth**: Free API key (strongly recommended). Without key: 240 req/min, 1,000/day per IP. With key: 240 req/min, 120,000/day.
- **Format**: JSON (Elasticsearch-based)
- **Key endpoints**: `/drug/event.json`, `/drug/label.json`, `/drug/ndc.json`, `/drug/drugsfda.json`, `/drug/shortages.json`
- **GenomeAI value**: Drug safety signals, labeling data, approval history. **High-value for pharmacogenomics.**

### 2.2 RxNorm API
- **URL**: `https://rxnav.nlm.nih.gov/REST/`
- **Data**: Drug names, ingredients, brands, NDC codes, drug-drug interactions, drug classification
- **Auth**: None required for most endpoints. No API key needed.
- **Rate limits**: 20 requests/second recommended
- **Format**: JSON, XML
- **Key endpoints**: `/rxcui.json`, `/drugs.json`, `/interaction/interaction.json`, `/ndcstatus.json`
- **GenomeAI value**: Drug name normalization, ingredient lookup, interaction checking. **Essential for clinical workflows.**

### 2.3 DrugBank
- **URL**: `https://go.drugbank.com` (data downloads), API via `https://api.drugbank.com`
- **Data**: 16,000+ drug entries, drug interactions, targets, pharmacology, chemistry, pathways
- **Auth**: Academic license (free for academic researchers). API key required for API access.
- **Restrictions**: Academic license is free but requires registration. Commercial use requires paid license. API key is needed.
- **Format**: XML, CSV, JSON, SQL (download); JSON (API)
- **GenomeAI value**: Gold standard for drug data. Free for academic use. **High-value if academic context.**

### 2.4 ChEMBL REST API
- **URL**: `https://www.ebi.ac.uk/chembl/api/data/`
- **Data**: 2.9M compounds, 24.5M bioactivity measurements, 18,552 targets, approved drugs, mechanisms of action, drug indications
- **Auth**: None required. No API key.
- **Rate limits**: Pagination-based (max 1000 per page). Be reasonable.
- **Format**: JSON, XML, SDF, CSV
- **Key endpoints**: `/molecule`, `/target`, `/assay`, `/activity`, `/drug`, `/drug_indication`, `/mechanism`, `/similarity/{smiles}/{cutoff}`, `/substructure/{smiles}`
- **GenomeAI value**: Bioactivity data, drug-target relationships, compound search. **Must-have for drug discovery.**

---

## 3. PROTEIN/STRUCTURE

### 3.1 UniProt REST API
- **URL**: `https://rest.uniprot.org`
- **Data**: Protein sequences, functional annotations, pathways, variants, structures, cross-references, ID mapping
- **Auth**: None required. No login needed.
- **Rate limits**: No hard limit published. Use pagination or streaming for large downloads.
- **Format**: JSON, XML, FASTA, TSV, RDF
- **Key endpoints**: `/uniprotkb/search?query=...`, `/uniprotkb/stream?query=...`, `/uniprotkb/{accession}`, `/idmapping`
- **GenomeAI value**: Central protein knowledge base. Sequence + function + structure + variant data. **Must-have.**

### 3.2 RCSB PDB (Protein Data Bank)
- **URL**: `https://data.rcsb.org` (Data API), `https://search.rcsb.org` (Search API), `https://www.rcsb.org/graphql` (GraphQL)
- **Data**: 200K+ experimentally determined 3D structures, ligands, binding sites, sequence alignments
- **Auth**: None required
- **Rate limits**: Dynamic. 429 on overload. Start with handful of req/sec.
- **Format**: JSON, mmCIF, PDB, SDF
- **Key endpoints**: `/rest/v1/core/entry/{pdb_id}`, `/rest/v1/core/polymer_entity/{pdb_id}/{entity_id}`, Search API for sequence/structure similarity
- **GenomeAI value**: 3D protein structures, binding site analysis, drug docking context. **High-value.**

### 3.3 AlphaFold DB
- **URL**: `https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}`
- **Data**: 241M+ predicted protein structures (pLDDT confidence, PAE matrices)
- **Auth**: None required. No API key.
- **Rate limits**: Exists but undocumented. 429 = wait 30 sec. Reasonable pacing.
- **Format**: mmCIF, PDB, BinaryCIF, JSON metadata
- **Key endpoints**: `/api/prediction/{uniprot_id}`, `/files/{entry_id}-model_v{ver}.cif`, `/files/{entry_id}-confidence_v{ver}.json`
- **License**: CC-BY-4.0 (free for academic and commercial use)
- **GenomeAI value**: Structure predictions for proteins without experimental structures. **Game-changer for functional genomics.**

---

## 4. LITERATURE

### 4.1 PubMed E-utilities (see NCBI above)
- Part of NCBI E-utilities (db=pubmed, db=pmc)
- **GenomeAI value**: Literature retrieval, abstract search, full-text (PMC) access. **Core integration.**

### 4.2 Europe PMC REST API
- **URL**: `https://www.ebi.ac.uk/europepmc/webservices/rest/`
- **Data**: 33M+ publications (PubMed + Agricola + EPO + more), 10.2M full-text, 6.5M open-access, text-mined annotations (genes, diseases, chemicals, GO terms)
- **Auth**: None required
- **Rate limits**: Be reasonable, no published hard limit
- **Format**: JSON, XML, Dublin Core
- **Key endpoints**: `/search?query=...`, `/search?query=...&resulttype=core` (full text), `/annotations_listByArticleIds`
- **GenomeAI value**: Broader coverage than PubMed, full-text access, text-mined biological entities. **High-value for literature RAG.**

### 4.3 Semantic Scholar API
- **URL**: `https://api.semanticscholar.org/graph/v1/`
- **Data**: 200M+ papers, citations, authors, SPECTER2 embeddings, recommendations, TLDRs
- **Auth**: Optional API key (1 RPS with key, shared 1000 RPS without). Free API key for higher limits.
- **Rate limits**: 1000 RPS shared (unauthenticated), 1 RPS per key (authenticated), higher by request
- **Format**: JSON
- **Key endpoints**: `/paper/search?query=...`, `/paper/{paperId}`, `/paper/{paperId}/citations`, `/paper/{paperId}/references`, `/recommendations/v1/papers/`
- **GenomeAI value**: Citation graphs, paper embeddings for semantic search, recommendations. **Excellent for literature RAG pipeline.**

---

## 5. CLINICAL

### 5.1 ClinicalTrials.gov API v2
- **URL**: `https://clinicaltrials.gov/api/v2/studies`
- **Data**: 500K+ clinical trials, eligibility criteria, outcomes, locations, sponsors, interventions, results
- **Auth**: None required. No API key.
- **Rate limits**: No published hard limit for anonymous use. Batch and cache.
- **Format**: JSON, CSV
- **Key endpoints**: `/studies?query.cond=...`, `/studies?query.intr=...`, `/studies/{nctId}`, `/stats/size`
- **GenomeAI value**: Drug trial status, eligibility, outcomes. **High-value for translational research.**

### 5.2 OHDSI/OMOP Common Data Model
- **URL**: Vocabulary downloads via `https://athena.ohdsi.org`. WebAPI for cohort queries (self-hosted).
- **Data**: Standardized vocabularies (SNOMED, ICD, RxNorm, LOINC, etc.), CDM for observational data
- **Auth**: Vocabulary downloads are free. WebAPI requires self-hosted infrastructure.
- **Format**: SQL DDLs, R packages, CSV vocabulary files
- **GenomeAI value**: Vocabulary standardization, concept mapping. **Important for clinical data interoperability.**

---

## 6. PATHWAY/FUNCTION

### 6.1 KEGG API
- **URL**: `https://rest.kegg.jp/`
- **Data**: Pathways, modules, orthology (KO), genes, genomes, compounds, reactions, diseases, drugs
- **Auth**: None required for academic use. **Non-commercial/academic only.**
- **Rate limits**: 3 req/sec. Exceeding = blocked.
- **Format**: Text (flat file), JSON (brite), KGML (pathways)
- **Key operations**: `/list`, `/find`, `/get`, `/link`, `/conv`, `/ddi` (drug-drug interactions)
- **GenomeAI value**: Pathway-level biological understanding. **Essential for functional genomics.**

### 6.2 Reactome Content Service
- **URL**: `https://reactome.org/ContentService/`
- **Data**: Curated, peer-reviewed biological pathways (human + 14 species), reactions, molecular interactions
- **Auth**: None required
- **Rate limits**: No published hard limit
- **Format**: JSON, OpenAPI (Swagger-documented)
- **Key endpoints**: `/data/event/{id}`, `/data/participants/{id}`, `/data/orthology/{id}`, `/data/query/{queryId}`
- **GenomeAI value**: Curated pathway data, pathway analysis, species comparison. **High-value.**

### 6.3 Reactome Analysis Service
- **URL**: `https://reactome.org/AnalysisService/`
- **Data**: Pathway enrichment analysis for gene/protein lists
- **Auth**: None required
- **Key endpoint**: POST gene list for pathway enrichment
- **GenomeAI value**: Enrichment analysis of gene sets. **Essential for analysis pipelines.**

### 6.4 Gene Ontology (AmiGO/GO API)
- **URL**: `http://api.geneontology.org/` (GOlr-based), GOlr endpoints at `http://golr-aux.geneontology.io/solr`
- **Data**: Gene annotations (biological process, molecular function, cellular component), GO terms, evidence codes
- **Auth**: None required
- **Format**: JSON
- **Key endpoints**: `/api/bioentity/function/{GO_TERM}`, search annotations with filtering by taxon, evidence, aspect
- **GenomeAI value**: Functional annotation of genes. **Essential for gene function analysis.**

---

## 7. DISEASE

### 7.1 OMIM API
- **URL**: `https://api.omim.org/api/`
- **Data**: 26,000+ gene-phenotype relationships, Mendelian disorders, allelic variants, clinical synopses, gene maps
- **Auth**: **API key required** (free for academic/research use). For-profit companies need a license.
- **Rate limits**: Entries limited to 20/request (with includes), 100/request for gene map
- **Format**: JSON, XML
- **Key endpoints**: `/entry/{mimNumber}`, `/search`, `/geneMap`, `/clinicalSynopsis`
- **GenomeAI value**: Gold standard for Mendelian genetics. **High-value but requires registration.**

### 7.2 Disease Ontology API
- **URL**: `https://api.disease-ontology.org/v1`
- **Data**: Standardized disease terms, relationships, cross-references
- **Auth**: None required
- **Format**: JSON (OpenAPI 3.1 documented)
- **GenomeAI value**: Disease term standardization. **Useful for NER and entity linking.**

### 7.3 MONDO Disease Ontology
- **URL**: GitHub releases (`https://github.com/monarch-initiative/mondo/releases`), OLS lookup at `https://www.ebi.ac.uk/ols4/ontologies/mondo`, BioThings API at `https://biothings.io`
- **Data**: Harmonized disease ontology merging OMIM, Orphanet, DOID, EFO, NCIT with precise equivalence axioms
- **Auth**: None required
- **Format**: OWL, OBO, JSON
- **GenomeAI value**: Cross-disease vocabulary mapping. **Important for data harmonization.**

---

## 8. CHEMICAL/COMPOUND

### 8.1 PubChem PUG-REST
- **URL**: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/`
- **Data**: 110M+ compounds, 300M+ substances, bioassays, chemical properties, structures, similarity/substructure search
- **Auth**: None required
- **Rate limits**: 5 req/sec (hard enforced). No API keys. Contact for higher volumes.
- **Format**: JSON, XML, SDF, CSV, PNG, TXT
- **Key endpoints**: `/compound/cid/{cid}/property/...`, `/compound/cid/{cid}/JSON`, `/compound/smiles/{smiles}/cids/JSON`, `/assay/aid/{aid}/JSON`
- **GenomeAI value**: Compound lookup, property calculation, structure search, bioactivity. **Must-have for pharmacogenomics.**

### 8.2 ChEMBL (see Section 2.4)
- Bioactivity data linking compounds to targets. **Complementary to PubChem.**

---

## 9. SEQUENCE

### 9.1 NCBI BLAST API
- **URL**: `https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi`
- **Data**: Sequence similarity search against NCBI databases (nr, nt, refseq, etc.)
- **Auth**: None required
- **Rate limits**: >100 searches/24hrs = slower queue or block. Interactive users prioritized.
- **Format**: HTML, XML, JSON2, Tabular, Text, CSV
- **Workflow**: PUT to submit (get RID), poll GET with RID, GET results
- **GenomeAI value**: Sequence homology search. **Core bioinformatics tool.**

### 9.2 EBI EMBOSS / Job Dispatcher
- **URL**: `https://www.ebi.ac.uk/Tools/services/rest/`
- **Data**: 50+ bioinformatics tools: Clustal Omega, FASTA, BLAST+, InterProScan, pairwise alignment (needle, water), sequence analysis (pepstats, transeq), RNA analysis
- **Auth**: None required (email parameter needed for job tracking)
- **Rate limits**: Be reasonable
- **Format**: JSON (results in various formats)
- **Key tools**: `/clustalo`, `/emboss_needle`, `/emboss_water`, `/phobius`, `/hmmer3-phmmer`, `/interproscan`
- **GenomeAI value**: Sequence alignment, functional annotation, protein analysis suite. **Excellent value - many tools in one API.**

---

## 10. VARIANT

### 10.1 ClinVar (see Section 1.5)
### 10.2 gnomAD (see Section 1.4)
### 10.3 dbSNP (see Section 1.6)

### 10.4 LOVD (Leiden Open Variation Database)
- **URL**: `https://api.lovd.nl/v2/` (central), individual installations at `https://www.lovd.nl/`
- **Data**: Gene-centered variant data, HGVS validation, variant-disease relationships from 300+ LOVD installations
- **Auth**: None required for central API
- **Rate limits**: 5 variants/second, 1 batch request/second
- **Format**: JSON
- **Key endpoints**: `/checkHGVS/{hgvs}`, `/getGeneData/{gene}`
- **GenomeAI value**: Curated gene-specific variant data, HGVS validation. **Useful for variant description normalization.**

---

## 11. LLM APIs (Cheapest for Research)

### 11.1 Ollama (Local - Self-hosted)
- **URL**: `http://localhost:11434` (local)
- **Cost**: FREE (zero marginal cost). Requires GPU (16GB+ VRAM recommended, 24GB comfortable).
- **Models**: Llama 3.3 70B, Mistral, Gemma, Qwen, DeepSeek, BioMistral, 100+ models
- **Throughput**: ~60-130 tok/s on RTX 4090
- **Best for**: Privacy-sensitive data, offline use, high sustained volume, zero-cost inference
- **Break-even**: Own GPU becomes cheaper than API at ~300-400M tokens/month
- **GenomeAI value**: For local/privacy-critical genomics data processing. **Best for MVP on-premise deployment.**

### 11.2 Groq (Free Tier)
- **URL**: `https://api.groq.com/openai/v1`
- **Cost**: **FREE** (no credit card). 30 RPM, 500K tokens/day on Llama 3.1 8B Instant.
- **Paid**: Llama 3.1 8B: $0.05/$0.08 per 1M tokens. Llama 4 Scout: $0.11/$0.18. Llama 3.3 70B: $0.59/$0.79.
- **Speed**: Hundreds of tok/s (LPU hardware, among fastest inference)
- **Best for**: Prototyping, speed-critical apps, batch processing
- **GenomeAI value**: Free tier for development. Fast inference for real-time genomics Q&A.

### 11.3 Cerebras (Free Tier)
- **URL**: `https://api.cerebras.ai/v1`
- **Cost**: **FREE** (no credit card). 1M tokens/day, 5-30 RPM.
- **Models**: gpt-oss-120B, zai-glm-4.7, Llama 3.1 70B
- **Best for**: Large prompts, high daily volume without cost
- **GenomeAI value**: 1M free tokens/day is generous for research prototypes.

### 11.4 Together AI
- **URL**: `https://api.together.xyz/v1`
- **Cost**: $0.05/$0.20 per 1M tokens (gpt-oss-20B). DeepSeek V4 Flash: $0.14/$0.28. Llama 3.3 70B: $1.04/$1.04.
- **Free**: Small starter credits on signup
- **Best for**: Open model fine-tuning, model catalog breadth (200+ models)
- **GenomeAI value**: Fine-tuning on biomedical data. Access to latest open models.

### 11.5 DeepSeek
- **URL**: `https://api.deepseek.com/v1`
- **Cost**: 5M free tokens on signup. DeepSeek V4: $0.30/$0.50 per 1M tokens (1M context).
- **Best for**: Long-context reasoning, chain-of-thought analysis
- **GenomeAI value**: 1M context window ideal for long genomic sequences/literature.

### 11.6 Google Gemini (Free Tier)
- **URL**: `https://generativelanguage.googleapis.com/v1beta`
- **Cost**: Free tier for Flash models (1,500 req/day after late-2025 cuts). Gemini 2.5 Flash free.
- **Best for**: Multi-modal analysis (text + images for variant visualization)
- **GenomeAI value**: Free baseline. Multi-modal capabilities.

### 11.7 OpenRouter (Aggregator)
- **URL**: `https://openrouter.ai/api/v1`
- **Cost**: ~30 free models. Paid models at various prices.
- **Best for**: Try many models with one API key
- **GenomeAI value**: Model comparison, fallback routing.

### 11.8 GitHub Models
- **URL**: `https://models.inference.ai.azure.com`
- **Cost**: **FREE** (GitHub account required). 50-150 req/day. GPT-4o, Llama, Mistral.
- **GenomeAI value**: Free access to GPT-4o for prototyping.

### 11.9 LLM7.io
- **URL**: `https://llm7.io/api`
- **Cost**: **FREE** (donor-supported). 30+ models. No published rate limits.
- **Best for**: Zero-cost inference at scale
- **GenomeAI value**: Backup free inference.

---

## 12. VECTOR DATABASES (for Biomedical RAG)

### 12.1 ChromaDB
- **URL**: `https://www.trychroma.com` (cloud) / `pip install chromadb` (local)
- **Cost**: **FREE** (open-source, self-hosted). Cloud has free tier.
- **Features**: Embedding storage, similarity search, metadata filtering
- **Best for**: Simplest setup, embedded mode, prototyping
- **GenomeAI value**: Easiest to integrate. Already used in biomedical RAG projects (longreads-rag, drug-discovery-rag-agent).

### 12.2 Qdrant
- **URL**: `https://qdrant.tech` / `docker run qdrant/qdrant` (local) / Cloud free tier
- **Cost**: **FREE** (open-source, self-hosted). Cloud: free tier available.
- **Features**: Dense + sparse vectors, multi-vector (ColBERT), filtering, recommendations, hybrid search (BM25 + dense)
- **Best for**: Production-grade, high-performance, hybrid retrieval
- **GenomeAI value**: **Best choice for biomedical RAG**. Already proven in biomedical-graphrag projects. Supports hybrid retrieval (dense + BM25 + reranking), metadata filtering by specialty/year, and constraint-based recommendations.

### 12.3 Weaviate
- **URL**: `https://weaviate.io` / `pip install weaviate-client`
- **Cost**: **FREE** (open-source, self-hosted). Cloud free tier.
- **Features**: Hybrid search, multi-tenancy, generative search, built-in vectorization
- **Best for**: Schema-heavy applications, multi-tenant deployments
- **GenomeAI value**: Good alternative to Qdrant with built-in vectorization.

### 12.4 FAISS (Facebook AI Similarity Search)
- **URL**: `https://github.com/facebookresearch/faiss`
- **Cost**: **FREE** (open-source library, not a server)
- **Features**: Billion-scale vector search, GPU acceleration, multiple index types
- **Best for**: When you need raw speed at scale and want to manage your own storage
- **GenomeAI value**: High-performance embedding search if building custom pipeline.

### 12.5 Milvus Lite
- **URL**: `https://milvus.io` / `pip install milvus-lite`
- **Cost**: **FREE** (open-source, Lite version runs in-process)
- **Features**: Distributed vector database, GPU support, hybrid search
- **Best for**: When you may need to scale to distributed setup later

---

## PRIORITY MATRIX FOR GenomeAI

### Tier 1 - Must Have (Core Integration)
| API | Why |
|-----|-----|
| NCBI E-utilities | Central hub for all biomedical data |
| Ensembl REST | Genome annotation backbone |
| gnomAD | Variant pathogenicity via allele frequency |
| ClinVar | Clinical variant interpretation |
| UniProt | Protein knowledge base |
| PubMed/Europe PMC | Literature foundation |
| ChEMBL | Drug-target-bioactivity triangle |
| PubChem | Compound data and search |
| RxNorm | Drug name normalization |

### Tier 2 - High Value
| API | Why |
|-----|-----|
| OpenFDA | Drug safety and labeling |
| RCSB PDB | 3D protein structures |
| AlphaFold DB | Predicted structures for everything |
| ClinicalTrials.gov | Translational research context |
| KEGG | Pathway-level understanding |
| Reactome | Curated pathways + enrichment |
| Gene Ontology | Functional annotation |
| Semantic Scholar | Citation graphs + embeddings |
| Cerebras/Groq | Free LLM inference |
| Qdrant | Vector DB for RAG |

### Tier 3 - Important
| API | Why |
|-----|-----|
| UCSC Genome Browser | Sequence extraction, track data |
| OMIM | Mendelian genetics (needs registration) |
| MONDO | Disease ontology harmonization |
| Disease Ontology | Disease term standardization |
| NCBI BLAST | Sequence homology |
| EBI EMBOSS | Suite of analysis tools |
| LOVD | HGVS validation, curated variants |
| ChromaDB | Simpler alternative to Qdrant |
| Ollama | Local LLM for privacy |

### Tier 4 - Nice to Have
| API | Why |
|-----|-----|
| OHDSI/OMOP | Clinical data standardization |
| DrugBank | Rich drug data (academic license needed) |
| LLM7.io | Backup free inference |
| DeepSeek | Long-context reasoning |
| OpenRouter | Multi-model access |
| GitHub Models | Free GPT-4o access |

---

## KEY ARCHITECTURE INSIGHTS

1. **Most APIs are truly free** - No auth, no keys, just rate limits. The biomedical API ecosystem is exceptionally open.
2. **NCBI is the center of gravity** - E-utilities connects to 38 databases. One integration unlocks massive value.
3. **Rate limits are manageable** - Most APIs allow 3-15 req/sec. With caching and batching, this is sufficient for real-time queries.
4. **Free LLMs are production-ready** - Groq + Cerebras free tiers provide enough capacity for MVP. Ollama for privacy.
5. **Qdrant is the best RAG vector DB** - Proven in biomedical use cases, supports hybrid retrieval, free and self-hostable.
6. **AlphaFold + UniProt + PDB** together provide complete structural coverage (predicted + experimental).
7. **Two literature sources beat one** - PubMed for breadth, Europe PMC for full-text, Semantic Scholar for citation graphs and embeddings.
