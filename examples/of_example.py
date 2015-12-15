import sys
from simdat.openface import oftools
from simdat.core import tools
from simdat.core import plot
from simdat.core import ml

"""
This is an example to run openface and classify the results.

$python of_example ACTION ACTION THRESHOLD

ACTION: action to do, rep/train(default)/test
METHOD: method of classifier, SVC(default)/RF/Neighbors
THRESHOLD: only needed if test is chosen as ACTION
           float between 0 to 1 (default: 0.4)

Tune other parameters in openface.json and ml.json
"""

pfs = ['openface.json', 'ml.json']
im = tools.IMAGE()
pl = plot.PLOT()
of = oftools.OpenFace(pfs=pfs)
mltl = ml.MLTools()

args = sys.argv[1:]

act = 'train'
if len(args) > 0:
    act = args[0]
print("Action: %s" % act)

method = 'SVC'
if len(args) > 1:
    method = args[1]
if method == 'RF':
    ml = ml.RFRun(pfs=pfs)
elif method == 'Neighbors':
    ml = ml.NeighborsRun(pfs=pfs)
else:
    ml = ml.SVMRun(pfs=pfs)

if act == 'rep':
    images = im.find_images()
    of.get_reps(images, output=True)

elif act == 'pca_multi':
    import numpy as np
    data = []
    root = '/tammy/viscovery/demo/db/'
    inf = root + 'train/train_homography.json'
    res = of.read_df(inf, dtype='train', group=False)
    pca_data = mltl.PCA(res['data'], method='Randomized')
    pca_data = np.array(pca_data).T
    data.append([pca_data[0], pca_data[1]])
    inf = root + 'train/train_perspective.json'
    res = of.read_df(inf, dtype='train', group=False)
    pca_data = mltl.PCA(res['data'], method='Randomized')
    pca_data = np.array(pca_data).T
    data.append([pca_data[0], pca_data[1]])
    pl.plot_classes(data)

elif act == 'pca':
    import numpy as np
    root = '/tammy/viscovery/demo/db/'
    inf = root + 'train/train_homography.json'
    data = []
    for i in range(0, 10):
        res = of.read_df(inf, dtype='train', group=False, selclass=i)
        p = [k for k, v in res['mapping'].iteritems() if v == i][0]
        print('-- %s --' % p)
        pca_data = mltl.PCA(res['data'], method='Randomized')
        pca_data = np.array(pca_data).T
        fname = p + '_pca.png'
        pl.plot_points(pca_data[0], pca_data[1], fname=fname)
        data.append([pca_data[0], pca_data[1]])
    pl.plot_classes(data)

elif act == 'train':
    root = '/tammy/viscovery/demo/db/'
    inf = root + 'train/train_homography.json'
    res = of.read_df(inf, dtype='train', group=False)
    mf = ml.run(res['data'], res['target'])

elif act == 'test':
    from datetime import date
    thre = 0.4
    if len(args) > 2:
        thre = float(args[2])
    print('Threshold applied %.2f' % thre)
    root = '/tammy/viscovery/demo/db/'
    mf = root + 'models/train_homography/' + method + '.pkl'
    # mf = "/tammy/viscovery/demo/20151126/full/outDir/classifier.pkl"
    inf = root + 'tests/tests_homography.json'
    mpf = root + 'models/train_affine/mapping.json'
    # mpf = '/tammy/viscovery/demo/20151126/full/outDir/mapping.json'
    print('Reading model from %s' % mf)
    print('Reading db from %s' % inf)
    print('Reading mappings from %s' % mpf)
    res = of.read_df(inf, dtype='test', mpf=mpf, group=True)
    model = ml.read_model(mf)
    # model = model[1]
    match = 0
    nwrong = 0
    today = date.today().strftime("%Y%m%d")
    new_home = '/tammy/viscovery/demo/images/matched/' + today
    for i in range(0, len(res['data'])):
        r1 = ml.test(res['data'][i], res['target'][i], model,
                     target_names=res['target_names'])
        cat = res['target'][i][0]
        found = False
        mis_match = False
        if r1['prob'] is None:
            for p in range(0, len(r1['predicted'])):
                if cat == r1['predicted'][p]:
                    path = res['path'][i]
                    pl.patch_rectangle_img(res['path'][i],
                                           res['pos'][i][p], new_name=None)
                    found = True
        else:
            for p in range(0, len(r1['prob'])):
                prob = r1['prob'][p]
                vmax = max(prob)
                imax = prob.argmax()
                if vmax > thre:
                    if imax == cat:
                        path = res['path'][i]
                        pl.patch_rectangle_img(res['path'][i],
                                               res['pos'][i][p],
                                               new_home=new_home)
                        found = True
                    else:
                        mis_match = True
        if found:
            match += 1
        if mis_match:
            nwrong += 1
    print('Matched rate %.2f' % (float(match)/float(len(res['data']))))
    print('Mis-matched rate %.2f' % (float(nwrong)/float(len(res['data']))))
