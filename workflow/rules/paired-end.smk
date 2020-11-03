# Paired-end snakemake rules imported in the main Snakefile.

# Pre Alignment Rules
rule rawfastqc:
    input:
        expand(join(workpath,"{name}.R1.fastq.gz"), name=samples),
        expand(join(workpath,"{name}.R2.fastq.gz"), name=samples)
    output:
        expand(join(workpath,"rawQC","{name}.R1_fastqc.zip"), name=samples),
        expand(join(workpath,"rawQC","{name}.R2_fastqc.zip"), name=samples)
    priority: 2
    params:
        rname='pl:rawfastqc',
        outdir=join(workpath,"rawQC"),
    threads: 32
    envmodules: config['bin'][pfamily]['tool_versions']['FASTQCVER']
    container: "docker://nciccbr/fastqc:v0.0.1"
    shell: """
    fastqc {input} -t {threads} -o {params.outdir};
    """


rule trim_pe:
    input:
        file1=join(workpath,"{name}.R1."+config['project']['filetype']),
        file2=join(workpath,"{name}.R2."+config['project']['filetype']),
    output:
        out1=temp(join(workpath,trim_dir,"{name}.R1.trim.fastq.gz")),
        out2=temp(join(workpath,trim_dir,"{name}.R2.trim.fastq.gz"))
    params:
        rname='pl:trim_pe',
        # Exposed Parameters: modify config/templates/tools.json to change defaults
        fastawithadaptersetd=config['bin'][pfamily]['tool_parameters']['FASTAWITHADAPTERSETD'],
        leadingquality=config['bin'][pfamily]['tool_parameters']['LEADINGQUALITY'],
        trailingquality=config['bin'][pfamily]['tool_parameters']['TRAILINGQUALITY'],
        minlen=config['bin'][pfamily]['tool_parameters']['MINLEN'],
    threads:32
    envmodules: config['bin'][pfamily]['tool_versions']['CUTADAPTVER']
    container: "docker://nciccbr/ccbr_cutadapt_1.18:v032219"
    shell: """
    cutadapt --pair-filter=any --nextseq-trim=2 --trim-n -n 5 -O 5 -q {params.leadingquality},{params.trailingquality} -m {params.minlen}:{params.minlen} -b file:{params.fastawithadaptersetd} -B file:{params.fastawithadaptersetd} -j {threads} -o {output.out1} -p {output.out2} {input.file1} {input.file2}
    """


rule fastqc:
    input:
        expand(join(workpath,trim_dir,"{name}.R1.trim.fastq.gz"), name=samples),
        expand(join(workpath,trim_dir,"{name}.R2.trim.fastq.gz"), name=samples)
    output:
        expand(join(workpath,"QC","{name}.R1.trim_fastqc.zip"), name=samples),
        expand(join(workpath,"QC","{name}.R2.trim_fastqc.zip"), name=samples),
        join(workpath,"QC","readlength.txt"),
    priority: 2
    params:
        rname='pl:fastqc',
        outdir=join(workpath,"QC"),
        getrl=join("workflow", "scripts", "get_read_length.py"),
    threads: 32
    envmodules: config['bin'][pfamily]['tool_versions']['FASTQCVER']
    container: "docker://nciccbr/fastqc:v0.0.1"
    shell: """
    fastqc {input} -t {threads} -o {params.outdir};
    python3 {params.getrl} {params.outdir} > {params.outdir}/readlength.txt  2> {params.outdir}/readlength.err
    """


rule fastq_screen:
    input:
        file1=join(workpath,trim_dir,"{name}.R1.trim.fastq.gz"),
        file2=join(workpath,trim_dir,"{name}.R2.trim.fastq.gz"),
    output:
        out1=join(workpath,"FQscreen","{name}.R1.trim_screen.txt"),
        out2=join(workpath,"FQscreen","{name}.R1.trim_screen.png"),
        out3=join(workpath,"FQscreen","{name}.R2.trim_screen.txt"),
        out4=join(workpath,"FQscreen","{name}.R2.trim_screen.png"),
        out5=join(workpath,"FQscreen2","{name}.R1.trim_screen.txt"),
        out6=join(workpath,"FQscreen2","{name}.R1.trim_screen.png"),
        out7=join(workpath,"FQscreen2","{name}.R2.trim_screen.txt"),
        out8=join(workpath,"FQscreen2","{name}.R2.trim_screen.png")
    params:
        rname='pl:fqscreen',
        outdir = join(workpath,"FQscreen"),
        outdir2 = join(workpath,"FQscreen2"),
        # Exposed Parameters: modify resources/fastq_screen{_2}.conf to change defaults
        # locations to bowtie2 indices
        fastq_screen_config=config['bin'][pfamily]['tool_parameters']['FASTQ_SCREEN_CONFIG'],
        fastq_screen_config2=config['bin'][pfamily]['tool_parameters']['FASTQ_SCREEN_CONFIG2'],
    threads: 24
    envmodules:
        config['bin'][pfamily]['tool_versions']['FASTQSCREENVER'],
        config['bin'][pfamily]['tool_versions']['PERLVER'],
        config['bin'][pfamily]['tool_versions']['BOWTIE2VER'],
    container: "docker://nciccbr/ccbr_fastq_screen_0.13.0:v032219"
    shell: """
    fastq_screen --conf {params.fastq_screen_config} --outdir {params.outdir} --threads {threads} --subset 1000000 --aligner bowtie2 --force {input.file1} {input.file2}
    fastq_screen --conf {params.fastq_screen_config2} --outdir {params.outdir2} --threads {threads} --subset 1000000 --aligner bowtie2 --force {input.file1} {input.file2}
    """


## Add later: create kraken2 docker image (use MiniKraken2_v1_8GB database)
## ftp://ftp.ccb.jhu.edu/pub/data/kraken2_dbs/old/minikraken2_v1_8GB_201904.tgz
#rule kraken_pe:
#    input:
#        fq1=join(workpath,trim_dir,"{name}.R1.trim.fastq.gz"),
#        fq2=join(workpath,trim_dir,"{name}.R2.trim.fastq.gz"),
#    output:
#        krakentaxa = join(workpath,kraken_dir,"{name}.trim.fastq.kraken_bacteria.taxa.txt"),
#        kronahtml = join(workpath,kraken_dir,"{name}.trim.fastq.kraken_bacteria.krona.html"),
#    params:
#        rname='pl:kraken',
#        prefix = "{name}",
#        outdir=join(workpath,kraken_dir),
#        bacdb=config['bin'][pfamily]['tool_parameters']['KRAKENBACDB'],
#        krakenver=config['bin'][pfamily]['tool_versions']['KRAKENVER'],
#        kronatoolsver=config['bin'][pfamily]['tool_versions']['KRONATOOLSVER'],
#    threads: 24
#    shell: """
#    module load {params.krakenver};
#    module load {params.kronatoolsver};
#    if [ ! -d {params.outdir} ];then mkdir {params.outdir};fi
#    cd /lscratch/$SLURM_JOBID;
#    cp -rv {params.bacdb} /lscratch/$SLURM_JOBID/;
#    kraken --db /lscratch/$SLURM_JOBID/`echo {params.bacdb}|awk -F "/" '{{print \$NF}}'` --fastq-input --gzip-compressed --threads {threads} --output /lscratch/$SLURM_JOBID/{params.prefix}.krakenout --preload --paired {input.fq1} {input.fq2}
#    kraken-translate --mpa-format --db /lscratch/$SLURM_JOBID/`echo {params.bacdb}|awk -F "/" '{{print \$NF}}'` /lscratch/$SLURM_JOBID/{params.prefix}.krakenout |cut -f2|sort|uniq -c|sort -k1,1nr > /lscratch/$SLURM_JOBID/{params.prefix}.krakentaxa
#    cut -f2,3 /lscratch/$SLURM_JOBID/{params.prefix}.krakenout | ktImportTaxonomy - -o /lscratch/$SLURM_JOBID/{params.prefix}.kronahtml
#    mv /lscratch/$SLURM_JOBID/{params.prefix}.krakentaxa {output.krakentaxa}
#    mv /lscratch/$SLURM_JOBID/{params.prefix}.kronahtml {output.kronahtml}
#    """


rule star1p:
    input:
        file1=join(workpath,trim_dir,"{name}.R1.trim.fastq.gz"),
        file2=join(workpath,trim_dir,"{name}.R2.trim.fastq.gz"),
        qcrl=join(workpath,"QC","readlength.txt"),
    output:
        out1= join(workpath,star_dir,"{name}.SJ.out.tab"),
        out3= temp(join(workpath,star_dir,"{name}.Aligned.out.bam")),
    params:
        rname='pl:star1p',
        prefix=join(workpath, star_dir, "{name}"),
        best_rl_script=join("workflow", "scripts", "optimal_read_length.py"),
        # Exposed Parameters: modify config/genomes/{genome}.json to change default
        stardir=config['references'][pfamily]['STARDIR'],
        # Exposed Parameters: modify config/templates/tools.json to change defaults
        filterintronmotifs=config['bin'][pfamily]['FILTERINTRONMOTIFS'],
        samstrandfield=config['bin'][pfamily]['SAMSTRANDFIELD'],
        filtertype=config['bin'][pfamily]['FILTERTYPE'],
        filtermultimapnmax=config['bin'][pfamily]['FILTERMULTIMAPNMAX'],
        alignsjoverhangmin=config['bin'][pfamily]['ALIGNSJOVERHANGMIN'],
        alignsjdboverhangmin=config['bin'][pfamily]['ALIGNSJDBOVERHANGMIN'],
        filtermismatchnmax=config['bin'][pfamily]['FILTERMISMATCHNMAX'],
        filtermismatchnoverlmax=config['bin'][pfamily]['FILTERMISMATCHNOVERLMAX'],
        alignintronmin=config['bin'][pfamily]['ALIGNINTRONMIN'],
        alignintronmax=config['bin'][pfamily]['ALIGNINTRONMAX'],
        alignmatesgapmax=config['bin'][pfamily]['ALIGNMATESGAPMAX'],
        adapter1=config['bin'][pfamily]['ADAPTER1'],
        adapter2=config['bin'][pfamily]['ADAPTER2'],
    threads: 32
    envmodules: config['bin'][pfamily]['tool_versions']['STARVER']
    container: "docker://nciccbr/ccbr_star_2.7.0f:v0.0.2"
    shell: """
    readlength=$(python {params.best_rl_script} {input.qcrl} {params.stardir})
    STAR --genomeDir {params.stardir}${{readlength}} \
    --outFilterIntronMotifs {params.filterintronmotifs} \
    --outSAMstrandField {params.samstrandfield} \
    --outFilterType {params.filtertype} \
    --outFilterMultimapNmax {params.filtermultimapnmax} \
    --alignSJoverhangMin {params.alignsjoverhangmin} \
    --alignSJDBoverhangMin {params.alignsjdboverhangmin} \
    --outFilterMismatchNmax {params.filtermismatchnmax} \
    --outFilterMismatchNoverLmax {params.filtermismatchnoverlmax} \
    --alignIntronMin {params.alignintronmin} \
    --alignIntronMax {params.alignintronmax} \
    --alignMatesGapMax {params.alignmatesgapmax} \
    --clip3pAdapterSeq {params.adapter1} {params.adapter2} \
    --readFilesIn {input.file1} {input.file2} \
    --readFilesCommand zcat \
    --runThreadN {threads} \
    --outFileNamePrefix {params.prefix}. \
    --outSAMtype BAM Unsorted \
    --alignEndsProtrude 10 ConcordantPair \
    --peOverlapNbasesMin 10
    """


rule sjdb:
    input:
        files=expand(join(workpath,star_dir,"{name}.SJ.out.tab"), name=samples)
    output:
        out1=join(workpath,star_dir,"uniq.filtered.SJ.out.tab")
    params:
        rname='pl:sjdb'
    shell: """
    cat {input.files} | sort | uniq | awk -F \"\\t\" '{{if ($5>0 && $6==1) {{print}}}}'| cut -f1-4 | sort | uniq | grep \"^chr\" | grep -v \"^chrM\" > {output.out1}
    """


rule star2p:
    input:
        file1=join(workpath,trim_dir,"{name}.R1.trim.fastq.gz"),
        file2=join(workpath,trim_dir,"{name}.R2.trim.fastq.gz"),
        tab=join(workpath,star_dir,"uniq.filtered.SJ.out.tab"),
        qcrl=join(workpath,"QC","readlength.txt"),
    output:
        out1=temp(join(workpath,star_dir,"{name}.p2.Aligned.sortedByCoord.out.bam")),
        out2=join(workpath,star_dir,"{name}.p2.ReadsPerGene.out.tab"),
        out3=join(workpath,bams_dir,"{name}.p2.Aligned.toTranscriptome.out.bam"),
        out4=join(workpath,star_dir,"{name}.p2.SJ.out.tab"),
        out5=join(workpath,log_dir,"{name}.p2.Log.final.out"),
    params:
        rname='pl:star2p',
        prefix=join(workpath, star_dir, "{name}.p2"),
        best_rl_script=join("workflow", "scripts", "optimal_read_length.py"),
        # Exposed Parameters: modify config/genomes/{genome}.json to change default
        stardir=config['references'][pfamily]['STARDIR'],
        # Exposed Parameters: modify config/templates/tools.json to change defaults
        filterintronmotifs=config['bin'][pfamily]['FILTERINTRONMOTIFS'],
        samstrandfield=config['bin'][pfamily]['SAMSTRANDFIELD'],
        filtertype=config['bin'][pfamily]['FILTERTYPE'],
        filtermultimapnmax=config['bin'][pfamily]['FILTERMULTIMAPNMAX'],
        alignsjoverhangmin=config['bin'][pfamily]['ALIGNSJOVERHANGMIN'],
        alignsjdboverhangmin=config['bin'][pfamily]['ALIGNSJDBOVERHANGMIN'],
        filtermismatchnmax=config['bin'][pfamily]['FILTERMISMATCHNMAX'],
        filtermismatchnoverlmax=config['bin'][pfamily]['FILTERMISMATCHNOVERLMAX'],
        alignintronmin=config['bin'][pfamily]['ALIGNINTRONMIN'],
        alignintronmax=config['bin'][pfamily]['ALIGNINTRONMAX'],
        alignmatesgapmax=config['bin'][pfamily]['ALIGNMATESGAPMAX'],
        adapter1=config['bin'][pfamily]['ADAPTER1'],
        adapter2=config['bin'][pfamily]['ADAPTER2'],
        outsamunmapped=config['bin'][pfamily]['OUTSAMUNMAPPED'],
        wigtype=config['bin'][pfamily]['WIGTYPE'],
        wigstrand=config['bin'][pfamily]['WIGSTRAND'],
        gtffile=config['references'][pfamily]['GTFFILE'],
        nbjuncs=config['bin'][pfamily]['NBJUNCS'],
    threads: 32
    envmodules: config['bin'][pfamily]['tool_versions']['STARVER']
    container: "docker://nciccbr/ccbr_star_2.7.0f:v0.0.2"
    shell: """
    readlength=$(python {params.best_rl_script} {input.qcrl} {params.stardir})
    STAR --genomeDir {params.stardir}${{readlength}} \
    --outFilterIntronMotifs {params.filterintronmotifs} \
    --outSAMstrandField {params.samstrandfield}  \
    --outFilterType {params.filtertype} \
    --outFilterMultimapNmax {params.filtermultimapnmax} \
    --alignSJoverhangMin {params.alignsjoverhangmin} \
    --alignSJDBoverhangMin {params.alignsjdboverhangmin} \
    --outFilterMismatchNmax {params.filtermismatchnmax} \
    --outFilterMismatchNoverLmax {params.filtermismatchnoverlmax} \
    --alignIntronMin {params.alignintronmin} \
    --alignIntronMax {params.alignintronmax} \
    --alignMatesGapMax {params.alignmatesgapmax} \
    --clip3pAdapterSeq {params.adapter1} {params.adapter2} \
    --readFilesIn {input.file1} {input.file2} \
    --readFilesCommand zcat \
    --runThreadN {threads} \
    --outFileNamePrefix {params.prefix}. \
    --outSAMunmapped {params.outsamunmapped} \
    --outWigType {params.wigtype} \
    --outWigStrand {params.wigstrand} \
    --sjdbFileChrStartEnd {input.tab} \
    --sjdbGTFfile {params.gtffile} \
    --limitSjdbInsertNsj {params.nbjuncs} \
    --quantMode TranscriptomeSAM GeneCounts \
    --outSAMtype BAM SortedByCoordinate \
    --alignEndsProtrude 10 ConcordantPair \
    --peOverlapNbasesMin 10
    mv {params.prefix}.Aligned.toTranscriptome.out.bam {workpath}/{bams_dir};
    mv {params.prefix}.Log.final.out {workpath}/{log_dir}
    """


rule qualibam:
    input:
        bamfile=join(workpath,bams_dir,"{name}.star_rg_added.sorted.dmark.bam"),
    output:
        report=join(workpath,"QualiMap","{name}","qualimapReport.html"),
    params:
        rname='pl:qualibam',
        outdir=join(workpath,"QualiMap","{name}"),
        gtfFile=config['references'][pfamily]['GTFFILE'],
    threads: 8
    envmodules: config['bin'][pfamily]['tool_versions']['QUALIMAPVER']
    container: "docker://nciccbr/ccbr_qualimap:v0.0.1"
    shell: """
    unset DISPLAY;
    qualimap bamqc -bam {input.bamfile} --feature-file {params.gtfFile} -outdir {params.outdir} -nt {threads} --java-mem-size=11G
    """


# Post Alignment Rules
rule rsem:
    input:
        file1=join(workpath,bams_dir,"{name}.p2.Aligned.toTranscriptome.out.bam"),
        file2=join(workpath,rseqc_dir,"{name}.strand.info")
    output:
        out1=join(workpath,degall_dir,"{name}.RSEM.genes.results"),
        out2=join(workpath,degall_dir,"{name}.RSEM.isoforms.results"),
    params:
        rname='pl:rsem',
        prefix=join(workpath,degall_dir,"{name}.RSEM"),
        rsemref=config['references'][pfamily]['RSEMREF'],
        annotate=config['references'][pfamily]['ANNOTATE'],
    envmodules:
        config['bin'][pfamily]['tool_versions']['RSEMVER'],
        config['bin'][pfamily]['tool_versions']['PYTHONVER'],
    container: "docker://nciccbr/ccbr_rsem_1.3.1:v032219"
    threads: 16
    shell: """
    # Get strandedness to calculate Forward Probability
    fp=`tail -n1 {input.file2} | awk '{{if($NF > 0.75) print "0.0"; else if ($NF<0.25) print "1.0"; else print "0.5";}}'`
    echo "Forward Probability Passed to RSEM: $fp"
    rsem-calculate-expression --no-bam-output --calc-ci --seed 12345  \
    --bam --paired-end -p {threads}  {input.file1} {params.rsemref} {params.prefix} --time \
    --temporary-folder /lscratch/$SLURM_JOBID --keep-intermediate-files --forward-prob=${{fp}} --estimate-rspd
    """


rule bam2bw_rnaseq_pe:
    input:
        bam=join(workpath,bams_dir,"{name}.star_rg_added.sorted.dmark.bam"),
        strandinfo=join(workpath,rseqc_dir,"{name}.strand.info")
    output:
        fbw=join(workpath,bams_dir,"{name}.fwd.bw"),
        rbw=join(workpath,bams_dir,"{name}.rev.bw")
    params:
        rname='pl:bam2bw',
        prefix="{name}",
        bashscript=join("workflow", "scripts", "bam2strandedbw.pe.sh")
    threads: 4
    shell: """
    sh {params.bashscript} {input.bam}

    # reverse files if method is not dUTP/NSR/NNSR ... ie, R1 in the direction of RNA strand.
    strandinfo=`tail -n1 {input.strandinfo}|awk '{{print $NF}}'`
    if [ `echo "$strandinfo < 0.25"|bc` -eq 1 ];then
    mv {output.fbw} {output.fbw}.tmp
    mv {output.rbw} {output.fbw}
    mv {output.fbw}.tmp {output.rbw}
    fi
    """