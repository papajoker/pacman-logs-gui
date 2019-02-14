# Maintainer: Papajoker <papajoke [at] archlinux [dot] info>
pkgname=pacman-logs-gui
pkgver=0.1.0
pkgrel=1
pkgdesc="pacman logs gui gtk"
arch=('any')
license=('GPL')
depends=('gtk3')
makedepends=('git')
source=('pacman-logs-gui' 'pacman-logs.py' 'pacman-logs.glade'  'alpmtransform.py' 'pacman-logs-gui.desktop')
noextract=()
md5sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
  #cd "$srcdir/$pkgname"
  mkdir -p "${pkgdir}/usr/lib/share/pacman-logs-gui"
  mkdir -p "${pkgdir}/usr/bin"
  mkdir -p "${pkgdir}/usr/share/applications"
  cp pacman-logs-gui "${pkgdir}/usr/bin/"
  cp pacman-logs.py "${pkgdir}/usr/lib/share/pacman-logs-gui"
  cp pacman-logs.glade  "${pkgdir}/usr/lib/share/pacman-logs-gui"
  cp alpmtransform.py "${pkgdir}/usr/lib/share/pacman-logs-gui"
  cp pacman-logs-gui.desktop "${pkgdir}/usr/share/applications"
}

